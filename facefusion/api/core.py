import os
import base64
import tempfile
import base64

from fastapi import FastAPI, APIRouter, Body
import uvicorn

import facefusion.globals as globals
from facefusion.core import conditional_process


app = FastAPI()
router = APIRouter()


def update_global_variables(params):
    for var_name, value in params.items():
        if value is not None:
            if hasattr(globals, var_name):
                setattr(globals, var_name, value)


def to_base64_str(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string.decode('utf-8')


def save_file(file_path: str, encoded_data: str):
    decoded_data = base64.b64decode(encoded_data)
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_path, "wb") as file:
        file.write(decoded_data)


def apply_args():
    from facefusion.vision import is_image, is_video, detect_image_resolution, detect_video_resolution, detect_video_fps, create_image_resolutions, create_video_resolutions, pack_resolution
    from facefusion.normalizer import normalize_fps
    if is_image(globals.target_path):
        output_image_resolution = detect_image_resolution(globals.target_path)
        output_image_resolutions = create_image_resolutions(output_image_resolution)
        if globals.output_image_resolution in output_image_resolutions:
            globals.output_image_resolution = globals.output_image_resolution
        else:
            globals.output_image_resolution = pack_resolution(output_image_resolution)
    if is_video(globals.target_path):
            output_video_resolution = detect_video_resolution(globals.target_path)
            output_video_resolutions = create_video_resolutions(output_video_resolution)
            if globals.output_video_resolution in output_video_resolutions:
                globals.output_video_resolution = globals.output_video_resolution
            else:
                globals.output_video_resolution = pack_resolution(output_video_resolution)
    if globals.output_video_fps or is_video(globals.target_path):
        globals.output_video_fps = normalize_fps(globals.output_video_fps) or detect_video_fps(globals.target_path)


@router.post("/")
async def process_frames(params = Body(...)) -> dict:
    update_global_variables(params)
    sources = params['sources']
    source_paths = []
    for i, source in enumerate(sources):
        source_path = os.path.join(tempfile.mkdtemp(), os.path.basename(f'source{i}.png'))
        save_file(source_path, source)
        source_paths.append(source_path)
    target = params['target']
    target_extension = params['target_extension']
    target_path = os.path.join(tempfile.mkdtemp(), os.path.basename(f'target{target_extension}'))
    save_file(target_path, target)
    globals.source_paths = source_paths
    globals.target_path = target_path
    globals.output_path = os.path.join(tempfile.mkdtemp(), os.path.basename(f'output{target_extension}'))
    apply_args()
    print(globals.source_paths)
    print(globals.target_path)
    print(globals.output_path)
    conditional_process()
    output = to_base64_str(globals.output_path)
    return {"output": output}


def launch():
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8000)