//
//  i1ProAdapterModule.c
//  i1ProAdapterModule
//
//  Created by Joseph Goldstone on 5/26/19.
//  Copyright © 2019 Arnold & Richter Cine Technik. All rights reserved.
//

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "i1ProAdapter.h"

#define ASSEMBLED_ERROR_TEXT_LENGTH 256
const size_t assembledErrorTextLength = ASSEMBLED_ERROR_TEXT_LENGTH;
static char assembledErrorTextBuffer[assembledErrorTextLength];

void
assembleErrorText(void)
{
    char* errorDescription;
    char* errorNumber;
    char* errorContext;
    iPAGetErrorDescription(&errorDescription, &errorNumber, &errorContext);
    snprintf(assembledErrorTextBuffer, sizeof(assembledErrorTextBuffer),
             "%s (error number %s; context %s)",
             errorDescription, errorNumber, errorContext);
    // iPAGetErrorDescription says it's our responsibility to delete these
    free(errorDescription);
    free(errorNumber);
    free(errorContext);
}

PyDoc_STRVAR(sdkVersionDoc, "get version of i1Pro SDK");
static
PyObject*
sdkVersion(PyObject* self)
{
    char* sdkVersionFromAdapter;
    bool sdkVersionResult = iPAGetSdkVersion(&sdkVersionFromAdapter);
    if (sdkVersionResult)
    {
        PyObject* result = Py_BuildValue("s", sdkVersionFromAdapter);
        free(sdkVersionFromAdapter);
        return result;
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
}

#define ASSEMBLED_ADAPTER_VERSION_LENGTH 256
const size_t assembledAdapterVersionLength = ASSEMBLED_ADAPTER_VERSION_LENGTH;
static char assembledAdapterVersionBuffer[assembledAdapterVersionLength];

PyDoc_STRVAR(adapterVersionDoc, "get version of i1ProAdapter");
static
PyObject*
adapterVersion(PyObject* self, PyObject* args)
{
    bzero(assembledAdapterVersionBuffer, assembledAdapterVersionLength);
    uint16_t major;
    uint16_t minor;
    uint16_t edit;
    char* build;
    iPAGetAdapterVersion(&major, &minor, &edit, &build);
    if (strlen(build) == 0)
    {
        snprintf(assembledAdapterVersionBuffer, assembledAdapterVersionLength, "%d.%d.%d", major, minor, edit);
    } else {
        snprintf(assembledAdapterVersionBuffer, assembledAdapterVersionLength, "%d.%d.%d (%s)", major, minor, edit, build);
    }
    return Py_BuildValue("s", assembledAdapterVersionBuffer);
}

const static uint16_t adapterModuleVersionMajor = 0;
const static uint16_t adapterModuleVersionMinor = 1;
const static uint16_t adapterModuleVersionEdit = 0;
const char* build = "pre-alpha";

#define ASSEMBLED_ADAPTER_MODULE_VERSION_LENGTH 256
const size_t assembledAdapterModuleVersionLength = ASSEMBLED_ADAPTER_MODULE_VERSION_LENGTH;
static char assembledAdapterModuleVersionBuffer[assembledAdapterModuleVersionLength];

PyDoc_STRVAR(adapterModuleVersionDoc, "get version of Python i1ProAdapter extension");
static
PyObject*
adapterModuleVersion(PyObject* self, PyObject* args)
{
    bzero(assembledAdapterModuleVersionBuffer, assembledAdapterModuleVersionLength);
    if (strlen(build) == 0)
    {
        snprintf(assembledAdapterModuleVersionBuffer, assembledAdapterModuleVersionLength, "%d.%d.%d",
        adapterModuleVersionMajor, adapterModuleVersionMinor, adapterModuleVersionEdit);
    } else {
        snprintf(assembledAdapterModuleVersionBuffer, assembledAdapterModuleVersionLength, "%d.%d.%d (%s)",
        adapterModuleVersionMajor, adapterModuleVersionMinor, adapterModuleVersionEdit, build);
    }
    return Py_BuildValue("s", assembledAdapterModuleVersionBuffer);
}

//PyDoc_STRVAR(attachDoc, "attach to meter");
///**
// @brief attach to an i1Pro meter
// @return None if no error; throws PyExc_IOError if any error
// */
//static
//PyObject*
//attach(PyObject* self)
//{
//    bool attachResult = iPAAttach();
//    if (attachResult)
//    {
//        return Py_None;
//    }
//    assembleErrorText();
//    return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
//}

PyDoc_STRVAR(openConnectionDoc, "open connection to meter");
/**
 @brief open connection to an i1Pro meter
 @return None if no error; throws PyExc_IOError if any error
 */
static
PyObject*
openConnection(PyObject* self, PyObject* args)
{
    int predicate;
    if (! PyArg_ParseTuple(args, "p", &predicate))
    {
        return PyErr_Format(PyExc_IOError, "Can't parse `debug' option to i1ProAdapterModule openConnection");
    }
    bool debug = (predicate == 1);
    bool openResult = iPAOpen(debug);
    if (openResult)
    {
        // TODO: figure out how to construct a string object that has all the debug output, and return it
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
}

PyDoc_STRVAR(meterIdDoc, "return identifying info for attached meter: make, model, serial number as a tuple");
/**
 @brief return meter identifying information.

 The identifying information is returned in the form of a tuple of make,
 model and serial number, each of which is a string.

 Exceptions:
 PyExc_XXX0 if no i1Pro device is attached.
 PyExc_XXX1 if multiple i1Pro devices are attached.

 */
static
PyObject*
meterId(PyObject* self)
{
    char* make;
    char* model;
    char* serialNumber;
    bool sdkResult = iPAGetMeterID(&make, &model, &serialNumber);
    if (sdkResult)
    {
        // TODO: fix leak of make, model and serial number strings returned from iPAGetMeterID
        return Py_BuildValue("(sss)", make, model, serialNumber);
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
}

PyDoc_STRVAR(spectralRangeDoc, "return tuple of spectroradiometer minimum and maximum sensitivity");
/**
 @brief return range(s) of wavelenghts meter can measure, as a tuple, in nm.
 @return tuple containing two integers
 */
static
PyObject*
spectralRange(PyObject* self)
{
    return Py_BuildValue("(ii)", 380, 730);
}

PyDoc_STRVAR(spectralResolutionDoc, "return tuple of spectroradiometer wavelength resolution");
/**
 @brief return spacing of returned spectral samples.
 @return tuple containing one integer
 */
static
PyObject*
spectralResolution(PyObject* self)
{
    return Py_BuildValue("(i)", 10);
}

//static
//PyObject*
//integrationTimeRange(PyObject* self, PyObject* args)
//{
//    PyObject* result = NULL;
//    // TODO: write body that assembles a two-element tuple of microseconds, e.g. ( 5e5, 1.8e8 )
//    return result;
//}

PyDoc_STRVAR(measurementModesDoc, "get supported measurement modes");
/**
 @brief return strings naming supported measurement modes
 @return tuple of strings naming supported measurement modes
 */
static
PyObject*
measurementModes(PyObject* self)
{
    return Py_BuildValue("(sss)", "emissive", "ambient", "reflective");
}

PyDoc_STRVAR(measurementModeDoc, "get currently-set measurement mode");
/**
 @brief return string naming currently-selected measurement mode
 @return string naming currently-selected measurement mode
 */
static
PyObject*
measurementMode(PyObject* self)
{
    iPAMeasurementMode_t mode;
    if (iPAGetMeasurementMode(&mode))
    {
        switch (mode)
        {
            case I1PRO_UNDEFINED_MEASUREMENT:
                return Py_BuildValue("(s)", "undefined");
            case I1PRO_EMISSIVE_SPOT_MEASUREMENT:
                return Py_BuildValue("(s)", "emissive");
            case I1PRO_AMBIENT_SPOT_MEASUREMENT:
                return Py_BuildValue("(s)", "ambient");
            case I1PRO_REFLECTIVE_SPOT_MEASUREMENT:
                return Py_BuildValue("(s)", "reflective");
            default:
                return Py_BuildValue("(s)", "unknown");
        }
    }
    return PyErr_Format(PyExc_IOError, "could not retrieve i1Pro current measurement mode");
}

PyDoc_STRVAR(setMeasurementModeDoc, "set measurement mode to one of 'emissive' or 'reflective'");
/**
 @brief select a measurement mode
 @return None
 */
static
PyObject*
setMeasurementMode(PyObject* self, PyObject* args)
{
    const char* mode;
    if (! PyArg_ParseTuple(args, "s", &mode))
    {
        return PyErr_Format(PyExc_IOError, "Unknown measurement mode '%s'; known modes are 'emissive', 'ambient', and 'reflective'", mode);
    }
    if (strcmp(mode, "emissive") == 0)
    {
        if (iPASetMeasurementMode(I1PRO_EMISSIVE_SPOT_MEASUREMENT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
        }
    }
    else if (strcmp(mode, "ambient") == 0)
    {
        if (iPASetMeasurementMode(I1PRO_AMBIENT_SPOT_MEASUREMENT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
        }
    }
    else if (strcmp(mode, "reflective") == 0)
    {
        if (iPASetMeasurementMode(I1PRO_REFLECTIVE_SPOT_MEASUREMENT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
        }
    }
    return PyErr_Format(PyExc_IOError, "Unknown measurement mode '%s'; known modes are 'emissive' and 'reflective'", mode);
}

PyDoc_STRVAR(calibrateDoc, "calibrate for currently selected measurement mode");
/**
 @brief calibrate the currentlu selected measurement mode
 @param waitForButtonPress boolean indicating whether to wait for user button press
 @return None
 */
static
PyObject*
calibrate(PyObject* self, PyObject* args)
{
    int predicate;
    if (! PyArg_ParseTuple(args, "p", &predicate))
    {
        return PyErr_Format(PyExc_IOError, "Can't parse `waitForButtonPress' argument to i1ProAdapterModule calibrate");
    }
    bool waitForButtonPress = (predicate == 1);
    if (iPACalibrate(waitForButtonPress))
    {
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s (calibrating)", assembledErrorTextBuffer);
}

PyDoc_STRVAR(triggerDoc, "trigger a measurement");
/**
 @brief select a measurement mode
 @return None
 */
static
PyObject*
trigger(PyObject* self, PyObject* args)
{
    if (iPATriggerMeasurement())
    {
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s (triggering measurement)", assembledErrorTextBuffer);
}

PyDoc_STRVAR(getCalibrationTimesDoc, "get the number of seconds since last calibration, and seconds remaining");
/**
 @brief get the number of seconds since the current mode was calibrated, and the number of seconds remaining
 @return tuple of strings with number of seconds since calibration and number of seconds remaining on calibration
 */
static
PyObject*
getCaliibrationTimes(PyObject* self, PyObject* args)
{
    char* since;
    char* until;
    printf("about to call iPAGetCalibrationTimes\n");
    fflush(NULL);
    if (iPAGetCalibrationTimes(&since, &until))
    {
        printf("back from iPAGetCalibrationTimes\n");
        fflush(NULL);
        printf("since and until are `%s' and `%s', respectively\n", since, until);
        fflush(NULL);
        return Py_BuildValue("(ss)", since, until);
    }
    return PyErr_Format(PyExc_IOError, "could not retrieve time since calibration and until calibration expiration from i1Pro");
}

const size_t COLORSPACE_COUNT = 8;
const iPAMeasurement_colorspace_t COLORSPACES[COLORSPACE_COUNT] =
{
    I1PRO_COLORSPACE_CIELab,
    I1PRO_COLORSPACE_CIELCh,
    I1PRO_COLORSPACE_CIELuv,
    I1PRO_COLORSPACE_CIELChuv,
    I1PRO_COLORSPACE_CIE_UV_Y1960,
    I1PRO_COLORSPACE_CIE_UV_Y1976,
    I1PRO_COLORSPACE_CIEXYZ,
    I1PRO_COLORSPACE_CIExyY
};
const size_t COLORSPACE_NAME_MAX_LENGTH = 16;
// Not required, but we choose to make these (used for communicating between the module
// adapter and the adapter) have the same values as do those in the i1Pro SDK itself.
char COLORSPACE_NAMES[COLORSPACE_COUNT][COLORSPACE_NAME_MAX_LENGTH] = {
    "CIELab",
    "CIELCh",
    "CIELuv",
    "CIELChuv",
    "CIEuvY1960",
    "CIEuvY1976",
    "CIEXYZ",
    "CIExyY"
};

bool
colorspaceForColorspaceName(const char* const colorspaceName, iPAMeasurement_colorspace_t* colorspace)
{
    size_t i = 0;
    for (i=0; i < COLORSPACE_COUNT; ++i)
    {
        if (strcmp(colorspaceName, COLORSPACE_NAMES[i]) == 0)
        {
            *colorspace = COLORSPACES[i];
            return true;
        }
    }
    return false;
}

bool
colorspaceNameForColorspace(iPAMeasurement_colorspace_t colorspace, char** colorspaceName)
{
    size_t i = 0;
    for (i=0; i < COLORSPACE_COUNT; ++i)
    {
        if (colorspace == COLORSPACES[i])
        {
            *colorspaceName = COLORSPACE_NAMES[i];
            return true;
        }
    }
    return false;
}

const size_t ILLUMINANT_COUNT = 11;
const iPAMeasurement_illuminant_t ILLUMINANTS[ILLUMINANT_COUNT] =
{
    I1PRO_ILLUMINANT_A,
    I1PRO_ILLUMINANT_B,
    I1PRO_ILLUMINANT_C,
    I1PRO_ILLUMINANT_D50,
    I1PRO_ILLUMINANT_D55,
    I1PRO_ILLUMINANT_D65,
    I1PRO_ILLUMINANT_D75,
    I1PRO_ILLUMINANT_F2,
    I1PRO_ILLUMINANT_F7,
    I1PRO_ILLUMINANT_F11,
    I1PRO_ILLUMINANT_EMISSION
};
const size_t ILLUMINANT_NAME_MAX_LENGTH = 16;
// Not required, but we choose to make these (used for communicating between the module
// adapter and the adapter) have the same values as do those in the i1Pro SDK itself.
char ILLUMINANT_NAMES[ILLUMINANT_COUNT][ILLUMINANT_NAME_MAX_LENGTH] = {
    "A",
    "B",
    "C",
    "D50",
    "D55",
    "D65",
    "D75",
    "F2",
    "F7",
    "F11",
    "Emission"
};

bool
illuminantForIlluminantName(const char* const illuminantName, iPAMeasurement_illuminant_t* illuminant)
{
    size_t i = 0;
    for (i=0; i < ILLUMINANT_COUNT; ++i)
    {
        if (strcmp(illuminantName, ILLUMINANT_NAMES[i]) == 0)
        {
            *illuminant = ILLUMINANTS[i];
            return true;
        }
    }
    return false;
}

bool
illuminantNameForIlluminant(iPAMeasurement_illuminant_t illuminant, char** illuminantName)
{
    size_t i = 0;
    for (i=0; i < ILLUMINANT_COUNT; ++i)
    {
        if (illuminant == ILLUMINANTS[i])
        {
            *illuminantName = ILLUMINANT_NAMES[i];
            return true;
        }
    }
    return false;
}

PyDoc_STRVAR(colorspacesDoc, "get a tuple of the names of the colorspaces in which colorimetric results can be returned");
/**
 @brief get a tuple of the names of the colorspaces in which colorimetric results can be returned
 @return tuple of the names of the colorspaces in which colorimetric results can be returned
 */
static
PyObject*
colorspaces(PyObject* self)
{
    // TODO reimolement using COLORSPACE_NAMES
    return Py_BuildValue("(ssssssss)", "CIELab", "CIELCh", "CIELuv", "CIELChhuv", "CIE_UV_Y1960",
    "CIE_UV_Y1976", "CIEXYZ", "CIExyY");
}

PyDoc_STRVAR(illuminantsDoc, "get a tuple of the names of the illuminants that can be used to convert spectral data to colorimetric data");
/**
 @brief get a tuple of the names of the illuminants that can be used to convert spectral data to colorimetric data
 @return tuple of the names of the illuminants that can be used to convert spectral data to colorimetric data
 */
static
PyObject*
illuminants(PyObject* self)
{
    // TODO reimplement using ILLUMINANT_NAMES
    return Py_BuildValue("(ssssssss)", "CIELab", "CIELCh", "CIELuv", "CIELChhuv", "CIE_UV_Y1960",
    "CIE_UV_Y1976", "CIEXYZ", "CIExyY");
}

PyDoc_STRVAR(colorspaceAndIlluminantDoc, "get the  colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data");
/**
 @brief get the colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data
 @return tuple of the colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data
 */
static
PyObject*
colorspaceAndIlluminant(PyObject* self, PyObject* args)
{
    iPAMeasurement_colorspace_t colorspace;
    iPAMeasurement_illuminant_t illuminant;
    if (iPAGetMeasurementColorspaceAndIlluminant(&colorspace, &illuminant))
    {
        char* colorspaceName;
        if (colorspaceNameForColorspace(colorspace, &colorspaceName))
        {
            char* illuminantName;
            if (illuminantNameForIlluminant(illuminant, &illuminantName))
            {
                return Py_BuildValue("(ss)", colorspaceName, illuminantName);
            }
            else
            {
                return PyErr_Format(PyExc_IOError, "unable to recognize illuminant");
            }
        }
        else
        {
            return PyErr_Format(PyExc_IOError, "unable to recognize colorspace");
        }
    }
    else
    {
        return PyErr_Format(PyExc_IOError, "unable to get i1Pro current colorspace and illuminant");
    }
}

PyDoc_STRVAR(setColorspaceAndIlluminantDoc, "set the colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data");
/**
 @brief setet the colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data
 @return None
 */
static
PyObject*
setColorspaceAndIlluminant(PyObject* self, PyObject* args)
{
    const char* colorspaceName;
    const char* illuminantName;
    if (! PyArg_ParseTuple(args, "ss", &colorspaceName, &illuminantName))
    {
        return PyErr_Format(PyExc_IOError, "unable to parse `colorspace' and/or 'illUninant' arguments");
    }
    iPAMeasurement_colorspace_t colorspace;
    iPAMeasurement_illuminant_t illuminant;
    if (colorspaceForColorspaceName(colorspaceName, &colorspace))
    {
        if (illuminantForIlluminantName(illuminantName, &illuminant))
        {
            if (iPASetMeasurementColorspaceAndIlluminant(colorspace, illuminant))
            {
                return Py_None;
            }
            else
            {
                return PyErr_Format(PyExc_IOError, "unable to set measurement colorspace and illuminant");
            }
        }
        else
        {
            return PyErr_Format(PyExc_IOError, "unable to recognize illuminant `%s'", illuminant);
        }
    }
    else
    {
        return PyErr_Format(PyExc_IOError, "unable to recognize colorspace `%s'", colorspace);
    }
}

PyDoc_STRVAR(measuredColorimetryDoc, "read colorimetry from a triggered measurement");
/**
 @brief get tristimulus colorimetry from a triggered measurement
 @return tuple of three floats representing measured tristimulus colorimetry
 */
static
PyObject*
measuredColorimetry(PyObject* self, PyObject* args)
{
    float tristimulus[3];
    if (iPAGetColorimetricMeasurementResults(tristimulus))
    {
        return Py_BuildValue("(fff)", tristimulus[0], tristimulus[1], tristimulus[2]);
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s (reading measured colorimetry)", assembledErrorTextBuffer);
}

PyDoc_STRVAR(measuredSpectrumDoc, "read spectrum from a triggered measurement");
/**
 @brief get spectral distribution from a triggered measurement
 @return tuple of 36 floats representing measured spectral distribution
 */
static
PyObject*
measuredSpectrum(PyObject* self, PyObject* args)
{
    const size_t spectrumSize = 36;
    float spectrum[spectrumSize];
    if (iPAGetSpectralMeasurementResults(spectrum))
    {
        return Py_BuildValue("(ffffffffffffffffffffffffffffffffffff)",
                             spectrum[0],
                             spectrum[1],
                             spectrum[2],
                             spectrum[3],
                             spectrum[4],
                             spectrum[5],
                             spectrum[6],
                             spectrum[7],
                             spectrum[8],
                             spectrum[9],
                             spectrum[10],
                             spectrum[11],
                             spectrum[12],
                             spectrum[13],
                             spectrum[14],
                             spectrum[15],
                             spectrum[16],
                             spectrum[17],
                             spectrum[18],
                             spectrum[19],
                             spectrum[20],
                             spectrum[21],
                             spectrum[22],
                             spectrum[23],
                             spectrum[24],
                             spectrum[25],
                             spectrum[26],
                             spectrum[27],
                             spectrum[28],
                             spectrum[29],
                             spectrum[30],
                             spectrum[31],
                             spectrum[32],
                             spectrum[33],
                             spectrum[34],
                             spectrum[35]);
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s (reading measured spectrum)", assembledErrorTextBuffer);
}

PyDoc_STRVAR(closeConnectionDoc, "close connection to meter");
static
PyObject*
closeConnection(PyObject* self, PyObject* args)
{
    int predicate;
    PyArg_ParseTuple(args, "p", &predicate);
    // TODO: check if the connection is open, and in that case, only close it if force is True
    // bool force = (predicate == 1);
    if (iPAClose(false))
    {
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
}

PyDoc_STRVAR(detachDoc, "detach from meter");
static
PyObject*
detach(PyObject* self, PyObject* args)
{
    return Py_None;
}

static PyMethodDef i1ProAdapterFuncs[] = {
    {"sdkVersion",                 (PyCFunction)sdkVersion,                 METH_NOARGS,  sdkVersionDoc},
    {"adapterVersion",             (PyCFunction)adapterVersion,             METH_NOARGS,  adapterVersionDoc},
    {"adapterModuleVersion",       (PyCFunction)adapterModuleVersion,       METH_NOARGS,  adapterModuleVersionDoc},
//    {"attach",                     (PyCFunction)attach,                     METH_NOARGS,  attachDoc},
    {"openConnection",             (PyCFunction)openConnection,             METH_VARARGS, openConnectionDoc},
    {"meterID",                    (PyCFunction)meterId,                    METH_NOARGS,  meterIdDoc},
    {"spectralRange",              (PyCFunction)spectralRange,              METH_NOARGS,  spectralRangeDoc},
    {"spectralResolution",         (PyCFunction)spectralResolution,         METH_NOARGS,  spectralResolutionDoc},
    {"measurementModes",           (PyCFunction)measurementModes,           METH_NOARGS,  measurementModesDoc},
    {"measurementMode",            (PyCFunction)measurementMode,            METH_NOARGS,  measurementModeDoc},
    {"setMeasurementMode",         (PyCFunction)setMeasurementMode,         METH_VARARGS, setMeasurementModeDoc},
    {"calibrate",                  (PyCFunction)calibrate,                  METH_VARARGS, calibrateDoc},
    {"trigger",                    (PyCFunction)trigger,                    METH_NOARGS,  triggerDoc},
    {"getCalibrationTimes",        (PyCFunction)getCaliibrationTimes,       METH_VARARGS, getCalibrationTimesDoc},
    {"colorspaces",                (PyCFunction)colorspaces,                METH_NOARGS,  colorspacesDoc},
    {"illuminants",                (PyCFunction)illuminants,                METH_NOARGS,  illuminantsDoc},
    {"colorspaceAndIlluminant",    (PyCFunction)colorspaceAndIlluminant,    METH_NOARGS,  colorspaceAndIlluminantDoc},
    {"setColorspaceAndIlluminant", (PyCFunction)setColorspaceAndIlluminant, METH_VARARGS, setColorspaceAndIlluminantDoc},
    {"illuminants",                (PyCFunction)illuminants,                METH_NOARGS,  illuminantsDoc},
    {"measuredColorimetry",        (PyCFunction)measuredColorimetry,        METH_NOARGS,  measuredColorimetryDoc},
    {"measuredSpectrum",           (PyCFunction)measuredSpectrum,           METH_NOARGS,  measuredSpectrumDoc},
    {"closeConnection",            (PyCFunction)closeConnection,            METH_VARARGS, closeConnectionDoc},
    {"detach",                     (PyCFunction)detach,                     METH_NOARGS,  detachDoc},
    {NULL}
};

static char i1ProAdapterDocs[] = "bridge between Python and i1ProAdapter";

static struct PyModuleDef i1ProAdapter_module = {
    PyModuleDef_HEAD_INIT,
    "i1ProAdapter",
    i1ProAdapterDocs,
    -1,
    i1ProAdapterFuncs
};



PyMODINIT_FUNC
PyInit_i1ProAdapter(void)
{
    return PyModule_Create(&i1ProAdapter_module);
}

// Thees three are the only ones that can be called without an attached device
// * get SDK version
// * attach
// * open
// * get module version
// * get adapter version
// * get meter ID
// get spectral measurement capabilities
// - * spectral range
// - * spectral resolution
// -- integration time range
// get time since last calibration
// get measurement modes
// * set measurement mode
// set color space for colorimetric measurement
// set bandwidth
// set sample averaging
// ? calibrate
// * trigger
// * read colorimetry
// read spectroradiometry
// close
// detach

