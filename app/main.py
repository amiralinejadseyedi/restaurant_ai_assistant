import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI, APIConnectionError, APIStatusError, APITimeoutError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import SessionLocal
from app.models import Product
import json


load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL")

if not API_KEY or not MODEL:
    raise ValueError(
        "OPENROUTER_API_KEY or OPENROUTER_MODEL is missing from .env"
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)


app = FastAPI(
    title="Restaurant AI Assistant",
    description="AI assistant for restaurant customers",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)




def search_products(db: Session, query: str):
    products = (
        db.query(Product)
        .filter(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%"),
            )
        )
        .filter(Product.is_in_stock.is_(True))
        .limit(10)
        .all()
    )

    return [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "currency": product.currency,
            "category": product.category,
            "description": product.description,
            "is_in_stock": product.is_in_stock,
        }
        for product in products
    ]

@app.get("/")
def home():
    return {
        "message": "Restaurant AI Assistant is running",
        "status": "ok",
    }


@app.post("/chat")
def chat(request: ChatRequest):

    db = SessionLocal()

    tools = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "جست‌وجوی محصولات رستوران در منوی رستوران",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "نام یا عبارت مورد جست‌وجوی محصول"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    }
    ]
    available_functions = {
        "search_products": search_products
    }
    try:
        messages = [
        {
        "role": "system",
        "content": (
            "تو دستیار هوش مصنوعی یک رستوران ایرانی هستی. "
            "فقط به زبان فارسی روان و طبیعی پاسخ بده. "
            "مودب، دقیق و مختصر باش. "
            "اگر برای پاسخ به اطلاعات واقعی منو، قیمت یا موجودی نیاز داری، "
            "از ابزارهای در دسترس استفاده کن. "
            "اگر محصول مرتبطی پیدا نشد، برای پیشنهاد دقیق سؤال تکمیلی بپرس. "
            "هرگز ادعا نکن اطلاعات واقعی منو را بررسی کرده‌ای، "
            "مگر اینکه واقعاً این اطلاعات را دریافت کرده باشی."
        )
        },
        {
        "role": "user",
        "content": request.question,
        },
        ]

        response = client.chat.completions.create(
            model=MODEL,
        messages=messages,
            tools=tools,
         tool_choice="auto",
         max_tokens=500,
         )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                print("ARGUMENTS:", repr(arguments))
                
                if tool_name not in available_functions:
                    raise HTTPException(
                        status_code=400,
                        detail="Unknown tool requested by AI",
                    )

                function = available_functions[tool_name]
                tool_result = function(db=db, **arguments)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
        if message.tool_calls:
            final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            )

            answer = final_response.choices[0].message.content.strip()

            return {"answer": answer}

        return {"answer": (message.content or "متأسفم، نتوانستم پاسخ مناسبی پیدا کنم.").strip()}


    except HTTPException:
        raise

    except APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="AI service timed out",
        )

    except APIConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to AI service",
        )

    except APIStatusError as error:
        if error.status_code == 401:
            detail = "AI service authentication failed"
        elif error.status_code == 429:
            detail = "AI service rate limit or quota exceeded"
        else:
            detail = "AI service returned an error"

        raise HTTPException(
            status_code=502,
            detail=detail,
        )

    except Exception as error:
        print("UNEXPECTED ERROR:", repr(error))
        raise HTTPException(
        status_code=502,
        detail="Unexpected AI service error",
        )

    finally:
        db.close()

