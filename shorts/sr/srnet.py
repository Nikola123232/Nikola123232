"""Real-ESRGAN 'realesr-general-x4v3' (SRVGGNetCompact) rebuilt as an ONNX graph from the published weights; runs on CPU with onnxruntime."""
import numpy as np, onnx, onnxruntime as ort
from onnx import helper, TensorProto, numpy_helper
def build(wpath="/home/user/Nikola123232/shorts/sr/rg_weights.npz"):
    w = np.load(wpath); nodes, inits = [], []
    def init(name, arr): inits.append(numpy_helper.from_array(np.ascontiguousarray(arr, np.float32), name))
    cur = "input"; i = 0
    while f"body.{i}.weight" in w.files:
        W = w[f"body.{i}.weight"]
        if W.ndim == 4:
            init(f"w{i}", W); init(f"b{i}", w[f"body.{i}.bias"]); out = f"c{i}"
            nodes.append(helper.make_node("Conv", [cur, f"w{i}", f"b{i}"], [out], pads=[1, 1, 1, 1], kernel_shape=[3, 3])); cur = out
        else:
            init(f"s{i}", W.reshape(-1, 1, 1)); out = f"p{i}"; nodes.append(helper.make_node("PRelu", [cur, f"s{i}"], [out])); cur = out
        i += 1
    nodes.append(helper.make_node("DepthToSpace", [cur], ["ps"], blocksize=4, mode="CRD"))
    init("scales", np.array([1, 1, 4, 4], np.float32)); init("roi", np.array([], np.float32))
    nodes.append(helper.make_node("Resize", ["input", "roi", "scales"], ["base"], mode="nearest"))
    nodes.append(helper.make_node("Add", ["ps", "base"], ["output"]))
    g = helper.make_graph(nodes, "srvgg", [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, "h", "w"])], [helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 3, "H", "W"])], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)]); m.ir_version = 9
    return m.SerializeToString()
class SR:
    def __init__(self):
        so = ort.SessionOptions(); so.intra_op_num_threads = 4; so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.s = ort.InferenceSession(build(), so, providers=["CPUExecutionProvider"])
    def __call__(self, rgb_uint8):
        x = (rgb_uint8.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        y = self.s.run(None, {"input": x})[0][0].transpose(1, 2, 0)
        return (np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8)
