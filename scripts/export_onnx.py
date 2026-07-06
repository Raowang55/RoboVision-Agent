"""Export models to ONNX format."""

import argparse


def main():
    parser = argparse.ArgumentParser(description="Export model to ONNX")
    parser.add_argument("--model", type=str, required=True, help="Path to PyTorch model")
    parser.add_argument("--output", type=str, default="outputs/model.onnx", help="Output path")
    parser.add_argument("--opset", type=int, default=17, help="ONNX opset version")
    parser.add_argument("--dynamic", action="store_true", help="Enable dynamic axes")
    args = parser.parse_args()

    print(f"Exporting {args.model} → {args.output} (opset={args.opset}, dynamic={args.dynamic})")
    print("(This is a placeholder — integrate torch.onnx.export here)")


if __name__ == "__main__":
    main()
