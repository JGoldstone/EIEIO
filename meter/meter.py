# Things that should be in a Python meter base class
# query capabilities:
# device identification
# - meter make
# - meter model
# - meter serial number
# - meter firmware version
# - meter SDK version
# - meter adapter version
# - module version
# measurement modes supported
# - emissive
# - ambient
# - reflective
# spectral ranges supported (tuples of start and end)
# spectral resolutions supported (bandwidth [PR has special term])
# integration time type
# - minimum
# - maximum (if this == minimum, then it's fixed integration time)
# colorimetric spaces natively supported
# last calibration time (dictionary, keyed per measurement mode)
