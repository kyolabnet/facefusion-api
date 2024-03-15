from typing import List, Any
import numpy as np
import onnxruntime as ort

def apply_execution_provider_options(execution_providers: List[str]) -> List[Any]:
	execution_providers_with_options : List[Any] = []

	for execution_provider in execution_providers:
		if execution_provider == 'CUDAExecutionProvider':
			execution_providers_with_options.append((execution_provider,
			{
				'cudnn_conv_algo_search': 'DEFAULT'
			}))
		else:
			execution_providers_with_options.append(execution_provider)
	return execution_providers_with_options


def check_cuda_availability():
    providers = ort.get_available_providers()
    print("Available providers:", providers)
    if 'CUDAExecutionProvider' in providers:
        print("CUDA is available in ONNX Runtime.")
    else:
        print("CUDA is NOT available. Please check your ONNX Runtime installation.")


def run_inference(model_path):
    session = ort.InferenceSession(model_path, providers=apply_execution_provider_options(['CUDAExecutionProvider', 'CPUExecutionProvider']))
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    dummy_input = np.random.randn(*input_shape).astype(np.float32)
    outputs = session.run(None, {input_name: dummy_input})
    print("Output:", outputs)

if __name__ == "__main__":
    check_cuda_availability()
    model_path = './.assets/models/codeformer.onnx'
    run_inference(model_path)ß