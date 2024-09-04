from math import pi

LIGHTMAP_LAYER_NAME = "LightmapUV"
LIGHTMAP_UV_ISLAND_MARGIN = 0.01

DISTANCE_MODELS = [("inverse", "Inverse drop off (inverse)",
                    "Volume will decrease inversely with distance"),
                   ("linear", "Linear drop off (linear)",
                   "Volume will decrease linearly with distance"),
                   ("exponential", "Exponential drop off (exponential)",
                   "Volume will decrease expoentially with distance")]


MAX_ANGLE = 2 * pi

PROJECTION_MODE = [("flat", "2D image (flat)", "Image will be shown on a 2D surface"),
                   ("360-equirectangular",
                    "Spherical (360-equirectangular)", "Image will be shown on a sphere")]

TRANSPARENCY_MODE = [("opaque", "No transparency (opaque)", "Alpha channel will be ignored"),
                     ("blend", "Gradual transparency (blend)",
                      "Alpha channel will be applied"),
                     ("mask", "Binary transparency (mask)",
                      "Alpha channel will be used as a threshold between opaque and transparent pixels")]

INTERPOLATION_MODES = [
    ("linear", "linear", ""),
    ("quadraticIn", "quadraticIn", ""),
    ("quadraticOut", "quadraticOut", ""),
    ("quadraticInOut", "quadraticInOut", ""),
    ("cubicIn", "cubicIn", ""),
    ("cubicOut", "cubicOut", ""),
    ("cubicInOut", "cubicInOut", ""),
    ("quarticIn", "quarticIn", ""),
    ("quarticOut", "quarticOut", ""),
    ("quarticInOut", "quarticInOut", ""),
    ("quinticIn", "quinticIn", ""),
    ("quinticOut", "quinticOut", ""),
    ("quinticInOut", "quinticInOut", ""),
    ("sinusoidalIn", "sinusoidalIn", ""),
    ("sinusoidalOut", "sinusoidalOut", ""),
    ("sinusoidalInOut", "sinusoidalInOut", ""),
    ("exponentialIn", "exponentialIn", ""),
    ("exponentialOut", "exponentialOut", ""),
    ("exponentialInOut", "exponentialIn", ""),
    ("circularIn", "circularIn", ""),
    ("circularOut", "circularOut", ""),
    ("circularInOut", "circularInOut", ""),
    ("elasticIn", "elasticIn", ""),
    ("elasticOut", "elasticOut", ""),
    ("elasticInOut", "elasticInOut", ""),
    ("backIn", "backIn", ""),
    ("backOut", "backOut", ""),
    ("backInOut", "backInOut", ""),
    ("bounceIn", "bounceIn", ""),
    ("bounceOut", "bounceOut", ""),
    ("bounceInOut", "bounceInOut", "")
]
