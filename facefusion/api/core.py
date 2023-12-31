import os
import base64
import time
from fastapi import FastAPI, APIRouter, Body

from facefusion.api.model import Params, print_globals
import facefusion.globals as globals
import facefusion.processors.frame.globals as frame_processors_globals
from facefusion import core
from facefusion.utilities import normalize_output_path

app = FastAPI()
router = APIRouter()

@router.post("/")
async def process_frames(params: Params = Body(...)) -> dict:
    delete_files_in_directory('temp/source')
    delete_files_in_directory('temp/target')
    delete_files_in_directory('temp/output')

    update_global_variables(params)
    
    if params.source and params.source_type:
        globals.source_path = f"temp/source/{params.user_id}-{int(time.time())}.{params.source_type}"
        save_file(globals.source_path, params.source)
    else:
        globals.source_path = ''

    globals.target_path = f"temp/target/{params.user_id}-{int(time.time())}.{params.target_type}"
    save_file(globals.target_path, params.target)

    globals.output_path = f"temp/output/{params.user_id}-{int(time.time())}.{params.target_type}"

    print_globals()

    try:
        core.api_conditional_process()
    except Exception as e:
        print(e)
        return {"message": "Error"}
    output = image_to_base64_str(globals.output_path)
    return {'output': output}

def update_global_variables(params: Params):
    for var_name, value in vars(params).items():
        if value is not None:
            if hasattr(globals, var_name):
                setattr(globals, var_name, value)
            elif hasattr(frame_processors_globals, var_name):
                setattr(frame_processors_globals, var_name, value)

def image_to_base64_str(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string.decode('utf-8')

def save_file(file_path: str, encoded_image: str):
    data = base64.b64decode(encoded_image)

    directory = os.path.dirname(file_path)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(file_path, "wb") as file:
        file.write(data)

def delete_files_in_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted {file_path}")


app.include_router(router)

def launch():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)