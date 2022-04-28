from math import radians


DISTACE_MODELS = [("inverse", "Inverse drop off (inverse)",
                  "Volume will decrease inversely with distance"),
                  ("linear", "Linear drop off (linear)",
                  "Volume will decrease linearly with distance"),
                  ("exponential", "Exponential drop off (exponential)",
                  "Volume will decrease expoentially with distance")]

MAX_ANGLE = radians(360.0)

PROJECTION_MODE = [("flat", "2D image (flat)", "Image will be shown on a 2D surface"),
                   ("360-equirectangular",
                    "Spherical (360-equirectangular)", "Image will be shown on a sphere")]

TRANSPARENCY_MODE = [("opaque", "No transparency (opaque)", "Alpha channel will be ignored"),
                     ("blend", "Gradual transparency (blend)",
                      "Alpha channel will be applied"),
                     ("mask", "Binary transparency (mask)",
                      "Alpha channel will be used as a threshold between opaque and transparent pixels")]
