from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from app.api import HTTPStatus, Auth
import gc

async def chat_endpoint(request: Request, token: str = Depends(Auth.get_bearer_token)):
    blue_vi_gpt_model = request.app.state.model
    prompt = None

    try:
        body = await request.json()
        prompt = body.get("prompt", "").strip()

        if not prompt:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST.value,
                content={"response": "No input provided."}
            )

        # Grammar correction and response generation
        grammar_correction_message = blue_vi_gpt_model.grammar_correction(prompt)
        bot_response = blue_vi_gpt_model.get_response(grammar_correction_message)

        return JSONResponse(
            status_code=HTTPStatus.OK.value,
            content={"response": bot_response}
        )

    except Exception as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content={"response": f"An error occurred: {str(e)}"}
        )
    
    finally:
        if prompt is not None:
            del prompt
        gc.collect()