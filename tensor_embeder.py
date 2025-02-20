import torch
import numpy as np


def serialize_to_tensor(serialized_board: list[list[list[int]]]) -> torch.Tensor:
    #Converts a serialized board representation into a PyTorch tensor.
    matrices = [np.array(channel) for channel in serialized_board]
    tensor_board = torch.stack([torch.tensor(matrix, dtype=torch.float32) for matrix in matrices])
    return tensor_board

def deserialize_from_tensor(tensor_board: torch.Tensor) -> list[list[list[int]]]:
    #Converts a PyTorch tensor back into a list-based board representation.
    return tensor_board.numpy().tolist()
