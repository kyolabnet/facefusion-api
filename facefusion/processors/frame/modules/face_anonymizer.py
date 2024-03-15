from typing import Any, List, Literal
from argparse import ArgumentParser
import cv2
import numpy

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion.face_analyser import get_one_face, get_average_face, get_many_faces, find_similar_faces, clear_face_analyser
from facefusion.face_helper import warp_face_by_face_landmark_5, paste_back
from facefusion.face_store import get_reference_faces
from facefusion.content_analyser import clear_content_analyser
from facefusion.typing import Face, FaceSet, VisionFrame, UpdateProcess, ProcessMode
from facefusion.vision import read_image, read_static_image, read_static_images, write_image
from facefusion.face_masker import create_occlusion_mask, clear_face_occluder

NAME = __name__.upper()


def get_frame_processor() -> Any:
	pass


def clear_frame_processor() -> None:
	pass


def get_options(key : Literal['model']) -> Any:
	pass


def set_options(key : Literal['model'], value : Any) -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	pass


def apply_args(program : ArgumentParser) -> None:
	pass


def pre_check() -> bool:
	return True


def post_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
	return True


def post_process() -> None:
	clear_frame_processor()
	clear_face_analyser()
	clear_content_analyser()
	clear_face_occluder()
	read_static_image.cache_clear()


def anonymize_face(source_face : Face, target_face : Face, temp_frame : VisionFrame) -> VisionFrame:
	crop_frame, affine_matrix = warp_face_by_face_landmark_5(temp_frame, target_face.kps, 'ffhq_512', (512 , 512))
	crop_mask_list = [ create_occlusion_mask(crop_frame) ]
	crop_frame = cv2.GaussianBlur(crop_frame, (99, 99), 0)
	crop_frame = cv2.GaussianBlur(crop_frame, (99, 99), 0)
	crop_mask = numpy.minimum.reduce(crop_mask_list).clip(0, 1)
	temp_frame = paste_back(temp_frame, crop_frame, crop_mask, affine_matrix)
	return temp_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(source_face : Face, reference_faces : FaceSet, temp_frame : VisionFrame) -> VisionFrame:
	if 'reference' in facefusion.globals.face_selector_mode:
		similar_faces = find_similar_faces(temp_frame, reference_faces, facefusion.globals.reference_face_distance)
		if similar_faces:
			for similar_face in similar_faces:
				temp_frame = anonymize_face(source_face, similar_face, temp_frame)
	if 'one' in facefusion.globals.face_selector_mode:
		target_face = get_one_face(temp_frame)
		if target_face:
			temp_frame = anonymize_face(source_face, target_face, temp_frame)
	if 'many' in facefusion.globals.face_selector_mode:
		many_faces = get_many_faces(temp_frame)
		if many_faces:
			for target_face in many_faces:
				temp_frame = anonymize_face(source_face, target_face, temp_frame)
	return temp_frame


def process_frames(source_paths : List[str], temp_frame_paths : List[str], update_progress : UpdateProcess) -> None:
	source_frames = read_static_images(source_paths)
	source_face = get_average_face(source_frames)
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	for temp_frame_path in temp_frame_paths:
		temp_frame = read_image(temp_frame_path)
		result_frame = process_frame(source_face, reference_faces, temp_frame)
		write_image(temp_frame_path, result_frame)
		update_progress()


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	source_frames = read_static_images(source_paths)
	source_face = get_average_face(source_frames)
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	target_frame = read_static_image(target_path)
	result_frame = process_frame(source_face, reference_faces, target_frame)
	write_image(output_path, result_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(source_paths, temp_frame_paths, process_frames)
