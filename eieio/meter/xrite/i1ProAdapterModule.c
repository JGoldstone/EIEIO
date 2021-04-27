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

// The following exceptions are raised by this module (hopefully a complete list,
// but if not just search for PyExc_):
// PyExc_Exception

#define ASSEMBLED_ERROR_TEXT_LENGTH 256
const size_t assembledErrorTextLength = ASSEMBLED_ERROR_TEXT_LENGTH;
static char assembledErrorTextBuffer[assembledErrorTextLength];

#define LAST_ERROR_NUMBER_TEXT_LENGTH 64
const size_t lastErrorNumberTextLength = LAST_ERROR_NUMBER_TEXT_LENGTH;
static char lastErrorNumberText[lastErrorNumberTextLength];

PyDoc_STRVAR(setLogOptionsDoc, "set logging options for i1ProAdapter ");
/**
 @brief set logging options for i1ProAdapter
 */
static
PyObject*
setLogOptions(PyObject* self, PyObject* args)
{
    int options = 0;
    if (! PyArg_ParseTuple(args, "i", &options))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse `options' option to i1ProAdapterModule setLogOptions");
    }
    LogOptions logOptions = (LogOptions)options;
    iPASetLoggingMask(logOptions);
    return Py_None;
}

bool
meterNotFound(void)
{
    return strcmp(lastErrorNumberText, "eDeviceNotConnected") == 0;
}

void
assembleErrorText(void)
{
    char* errorDescription;
    char* errorNumber;
    char* errorContext;
    iPAGetErrorDescription(&errorDescription, &errorNumber, &errorContext);
    strncpy(lastErrorNumberText, errorNumber, lastErrorNumberTextLength);
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
sdkVersion(PyObject* self, PyObject* args)
{
    char* meterType = NULL;
    i1Pro_t i1ProType = PRE_I1PRO3;
    char* sdkVersionFromAdapter;
    if (! PyArg_ParseTuple(args, "s", &meterType))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse `i1ProType' option to i1ProAdapterModule sdkVersion");
    }
    for (size_t i = 0; i < strlen(meterType); ++i) { meterType[i] = tolower(meterType[i]); }
    if (strcmp(meterType, "i1pro") == 0 || (strcmp(meterType, "i1pro2") == 0))
    {
        i1ProType = PRE_I1PRO3;
    } else if (strcmp(meterType, "i1pro3") == 0 || strcmp(meterType, "i1pro3+") == 0) {
        i1ProType = I1PRO3;
    } else {
        flushingFprintf(stdout, "meter type not identified in i1ProAdapterModule sdkVersion+\n");
            return PyErr_Format(PyExc_ValueError, "unrecognized i1Pro type `%s'; "
			    "recognized types are i1Pro, i1Pro2, i1Pro3, i1Pro3+", meterType);
    }
    if (iPAGetSdkVersion(i1ProType, &sdkVersionFromAdapter))
    {
        PyObject* result = Py_BuildValue("s", sdkVersionFromAdapter);
        free(sdkVersionFromAdapter);
        return result;
    }
    flushingFprintf(stdout, "could not get SDK version from lowest-level\n");
    assembleErrorText();
    return PyErr_Format(PyExc_Exception, "%s", assembledErrorTextBuffer);
}

#define ASSEMBLED_ADAPTER_VERSION_LENGTH 256
const size_t assembledAdapterVersionLength = ASSEMBLED_ADAPTER_VERSION_LENGTH;
static char assembledAdapterVersionBuffer[assembledAdapterVersionLength];

PyDoc_STRVAR(adapterVersionDoc, "get version of i1ProAdapter");
static
PyObject*
adapterVersion(PyObject* self)
{
    bzero(assembledAdapterVersionBuffer, assembledAdapterVersionLength);
    uint16_t major;
    uint16_t minor;
    uint16_t edit;
    char* build;
    iPAGetAdapterVersion(&major, &minor, &edit, &build);
    snprintf(assembledAdapterVersionBuffer, assembledAdapterVersionLength,
            "%d.%d.%d %s", major, minor, edit, strlen(build) > 0 ? build : "");
    PyObject* result = Py_BuildValue("s", assembledAdapterVersionBuffer);
    free(build);
    return result;
}

#define ASSEMBLED_ADAPTER_MODULE_VERSION_LENGTH 256
const size_t assembledAdapterModuleVersionLength = ASSEMBLED_ADAPTER_MODULE_VERSION_LENGTH;
static char assembledAdapterModuleVersionBuffer[assembledAdapterModuleVersionLength];

const static uint16_t adapterModuleVersionMajor = 0;
const static uint16_t adapterModuleVersionMinor = 2;
const static uint16_t adapterModuleVersionEdit = 0;
const char* build = "pre-alpha";

PyDoc_STRVAR(adapterModuleVersionDoc, "get version of Python i1ProAdapter extension");
static
PyObject*
adapterModuleVersion(PyObject* self)
{
    bzero(assembledAdapterModuleVersionBuffer, assembledAdapterModuleVersionLength);
    snprintf(assembledAdapterModuleVersionBuffer,
             assembledAdapterModuleVersionLength,
             "%d.%d.%d %s",
             adapterModuleVersionMajor,
			 adapterModuleVersionMinor,
			 adapterModuleVersionEdit, build);
    return Py_BuildValue("s", assembledAdapterModuleVersionBuffer);

}

PyDoc_STRVAR(meterIdDoc, "return identifying info for attached meter: make, model, "
                         "serial number as a tuple");
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
meterId(PyObject* self, PyObject* args)
{
    const char* meterName = NULL;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse meterName option to i1ProAdapterModule meterId");
    }
    char* make;
    char* model;
    char* serialNumber;
    if (iPAGetMeterID(meterName, &make, &model, &serialNumber))
    {
//        flushingFprintf(stdout, "meter name is %s, make %s, model %s, serialNumber %s\n",
//                        meterName, make, model, serialNumber);
        PyObject* result =  Py_BuildValue("(sss)", make, model, serialNumber);
        free(make);
        free(model);
        free(serialNumber);
        return result;
    }
    assembleErrorText();
    return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_IOError, "%s", assembledErrorTextBuffer);
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
    uint16_t numLambdas;
    uint16_t minLambda;
    uint16_t incLambda;
    iPAGetSpectralMeasurementCapabilities(&numLambdas, &minLambda, &incLambda);
    return Py_BuildValue("(ii)", minLambda, minLambda + (numLambdas - 1) * incLambda);
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
    return Py_BuildValue("i", 10);
}

PyDoc_STRVAR(populateRegistriesDoc, "populate the registry of known meters");
/**
 @brief populate the registry of known meters.
 */
static
PyObject*
populateRegistries(PyObject* self)
{
    iPAPopulateRegistries();
    return Py_None;
}

PyDoc_STRVAR(meterNamesAndModelsDoc, "returns a list tuples of known meters and their models (i1Pro, i1Pro2, &c");
/**
 @brief return the list of known meters.
 */
static
PyObject*
meterNamesAndModels(PyObject* self)
{
    size_t numMeterNames;
    char** meterNames;
    iPAGetMeterNames(&numMeterNames, &meterNames);
    PyObject* namesAndModels = PyList_New(0);
    if (namesAndModels == NULL)
    {
        return PyErr_Format(PyExc_Exception, "could not allocate zero-length "
                            "list in meterNamesAndModels");
    }
    for (size_t i = 0; i < numMeterNames; ++i)
    {
        char* make = "";
        char* model = "";
        char* serialNumber = "";
        if (! iPAGetMeterID(meterNames[i], &make, &model, &serialNumber))
        {
            return PyErr_Format(PyExc_Exception, "could not retrieve meter ID "
                                "information for meter `%s' in "
                                "meterNamesAndModels", meterNames[i]);
        }
        PyObject* nameAndModel = Py_BuildValue("(ss)", meterNames[i], model);
        if (nameAndModel == NULL)
        {
            return PyErr_Format(PyExc_Exception, "could not build meter name, "
                                "model tuple in meterNamesAndModels");
        }
        if (PyList_Append(namesAndModels, nameAndModel) == -1)
        {
            return PyErr_Format(PyExc_Exception, "could not append meter name, "
                                "model tuple for meter `%s' to meter names and "
                                "models list in meterNamesAndModels",
                                meterNames[i]);
        }
        free(make);
        free(model);
        free(serialNumber);
        free(meterNames[i]);
        meterNames[i] = NULL;
    }
    free(meterNames);
    return namesAndModels;
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
measurementMode(PyObject* self, PyObject* args)
{
    const char* meterName = NULL;
    iPAMeasurementMode_t mode;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse meterName option to i1ProAdapterModule meterId");
    }
    if (iPAGetMeasurementMode(meterName, &mode))
    {
        switch (mode)
        {
	case IPA_MM_UNDEFINED:
	    return Py_BuildValue("(s)", "undefined");
	case IPA_MM_EMISSIVE_SPOT:
	    return Py_BuildValue("(s)", "emissive");
	case IPA_MM_AMBIENT_SPOT:
	    return Py_BuildValue("(s)", "ambient");
	case IPA_MM_REFLECTIVE_SPOT:
	    return Py_BuildValue("(s)", "reflective");
	default:
	    return Py_BuildValue("(s)", "unknown");
        }
    }
    assembleErrorText();
    return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
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
    const char* meterName;
    const char* mode;
    if (! PyArg_ParseTuple(args, "ss", &meterName, &mode))
    {
        return PyErr_Format(PyExc_IOError, "could not parse meter name and/or measurement mode; "
                            "known modes are 'emissive', 'ambient', and 'reflective'");
    }
    if (strcmp(mode, "emissive") == 0)
    {
        if (iPASetMeasurementMode(meterName, IPA_MM_EMISSIVE_SPOT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
        }
    }
    else if (strcmp(mode, "ambient") == 0)
    {
        if (iPASetMeasurementMode(meterName, IPA_MM_AMBIENT_SPOT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
        }
    }
    else if (strcmp(mode, "reflective") == 0)
    {
        if (iPASetMeasurementMode(meterName, IPA_MM_REFLECTIVE_SPOT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
        }
    }
    return PyErr_Format(PyExc_ValueError, "Unknown measurement mode '%s'; known modes "
                        "are 'emissive', 'ambient' and 'reflective'", mode);
}

PyDoc_STRVAR(observersDoc, "get supported standard observers");
/**
 @brief return strings naming supported standard observers
 @return tuple of strings naming supported standard observers
 */
static
PyObject*
observers(PyObject* self)
{
    return Py_BuildValue("(ss)", "TWO_DEGREE_1931", "TEN_DEGREE_1964");
}

PyDoc_STRVAR(observerDoc, "get currently-set observer");
/**
 @brief return string naming currently-selected observer
 @return string naming currently-selected observer
 */
static
PyObject*
observer(PyObject* self, PyObject* args)
{
    const char* meterName;
    iPAObserver_t observer;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse meterName option to i1ProAdapterModule observer");
    }
    if (iPAGetObserver(meterName, &observer))
    {
        switch (observer)
        {
	case IPA_OB_UNDEFINED:
	    return Py_BuildValue("(s)", "undefined");
	case IPA_OB_TWO_DEGREE_1931:
	    return Py_BuildValue("(s)", "CIE_TWO_DEGREE_1931");
	case IPA_OB_TEN_DEGREE_1964:
	    return Py_BuildValue("(s)", "CIE_TEN_DEGREE_1964");
	default:
	    return Py_BuildValue("(s)", "unknown");
        }
    }
    return PyErr_Format(PyExc_IOError, "could not retrieve i1Pro current observer");
}

PyDoc_STRVAR(setObserverDoc, "set observer to either CIE 1932 2º or CIE 1964 10º");
/**
 @brief select a standard observer
 @return None
 */
static
PyObject*
setObserver(PyObject* self, PyObject* args)
{
    const char* meterName;
    const char* observer;
    if (! PyArg_ParseTuple(args, "ss", &meterName, &observer))
    {
        return PyErr_Format(PyExc_IOError, "i1ProAdapter cannot parse argument to setObserver as a string");
    }
    if (strcmp(observer, "CIE_TWO_DEGREE_1931") == 0)
    {
        if (iPASetObserver(meterName, IPA_OB_TWO_DEGREE_1931))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(meterNotFound()
				? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
        }
    }
    else if (strcmp(observer, "CIE_TEN_DEGREE_1964") == 0)
    {
        if (iPASetObserver(meterName, IPA_OB_TEN_DEGREE_1964))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(meterNotFound()
				? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
        }
    }
    return PyErr_Format(PyExc_ValueError, "Unknown observer '%s'; known observers "
                        "are 'CIE_TWO_DEGREE_1931' and 'CIE_TEN_DEGREE_1964'", observer);
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
    const char* meterName;
    int predicate;
    if (! PyArg_ParseTuple(args, "sp", &meterName, &predicate))
    {
        return PyErr_Format(PyExc_IOError, "Can't parse meterName and/or "
                            "`waitForButtonPress' argument to i1ProAdapterModule calibrate");
    }
    bool waitForButtonPress = (predicate == 1);
    if (iPACalibrate(meterName, waitForButtonPress))
    {
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
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
    const char* meterName;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse meterName option to i1ProAdapterModule trigger");
    }
    if (iPATriggerMeasurement(meterName))
    {
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
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
    const char* meterName;
    IPA_Integer since;
    IPA_Integer until;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse meterName option to i1ProAdapterModule trigger");
	}
    if (iPAGetCalibrationTimes(meterName, &since, &until))
    {
        // flushingFprintf(stdout, "back from iPAGetCalibrationTimes, since and until are `%d' and `%d', respectively\n", since, until);
        return Py_BuildValue("(dd)", since, until);
    }
    return PyErr_Format(PyExc_IOError, "could not retrieve time since calibration and until calibration expiration from i1Pro");
}

const size_t COLOR_SPACE_COUNT = 8;
const iPAColorSpace_t COLOR_SPACES[COLOR_SPACE_COUNT] =
{
    IPA_CS_CIELab,
    IPA_CS_CIELCh,
    IPA_CS_CIELuv,
    IPA_CS_CIELChuv,
    IPA_CS_CIE_uv_Y1960,
    IPA_CS_CIE_uPvP_Y1976,
    IPA_CS_CIEXYZ,
    IPA_CS_CIExyY
};
const size_t COLOR_SPACE_NAME_MAX_LENGTH = 16;
// Not required, but we choose to make these (used for communicating between the module
// adapter and the adapter) have the same values as do those in the i1Pro SDK itself.
char COLOR_SPACE_NAMES[COLOR_SPACE_COUNT][COLOR_SPACE_NAME_MAX_LENGTH] = {
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
colorSpaceForColorSpaceName(const char* const colorSpaceName, iPAColorSpace_t* colorSpace)
{
    size_t i = 0;
    for (i=0; i < COLOR_SPACE_COUNT; ++i)
    {
        if (strcmp(colorSpaceName, COLOR_SPACE_NAMES[i]) == 0)
        {
            *colorSpace = COLOR_SPACES[i];
            return true;
        }
    }
    return false;
}

bool
colorSpaceNameForColorSpace(iPAColorSpace_t colorSpace, char** colorSpaceName)
{
    size_t i = 0;
    for (i=0; i < COLOR_SPACE_COUNT; ++i)
    {
        if (colorSpace == COLOR_SPACES[i])
        {
            *colorSpaceName = COLOR_SPACE_NAMES[i];
            return true;
        }
    }
    return false;
}

const size_t ILLUMINANT_COUNT = 11;
const iPAIlluminant_t ILLUMINANTS[ILLUMINANT_COUNT] =
{
    IPA_IL_A,
    IPA_IL_B,
    IPA_IL_C,
    IPA_IL_D50,
    IPA_IL_D55,
    IPA_IL_D65,
    IPA_IL_D75,
    IPA_IL_F2,
    IPA_IL_F7,
    IPA_IL_F11,
    IPA_IL_EMISSION
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
illuminantForIlluminantName(const char* const illuminantName, iPAIlluminant_t* illuminant)
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
illuminantNameForIlluminant(iPAIlluminant_t illuminant, char** illuminantName)
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

PyDoc_STRVAR(colorSpacesDoc, "get a tuple of the names of the colorspaces in which colorimetric results can be returned");
/**
 @brief get a tuple of the names of the colorspaces in which colorimetric results can be returned
 @return tuple of the names of the colorspaces in which colorimetric results can be returned
 */
static
PyObject*
colorSpaces(PyObject* self)
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


PyDoc_STRVAR(colorSpaceDoc, "get the color space in which colorimetric results will be returned");
/**
 @brief get the color space in which colorimetric results will be returned
 @return the color space in which colorimetric results will be returned
 */
static
PyObject*
colorSpace(PyObject* self, PyObject* args)
{
    const char* meterName;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse meterName option to i1ProAdapterModule colorSpace");
    }
    iPAColorSpace_t colorSpace;
    if (iPAGetColorSpace(meterName, &colorSpace))
    {
        char* colorSpaceName;
        if (colorSpaceNameForColorSpace(colorSpace, &colorSpaceName))
        {
            return Py_BuildValue("s", colorSpaceName);
        }
        else
        {
            return PyErr_Format(PyExc_IOError, "unable to recognize color space");
        }
    }
    else
    {
        return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
    }
}

PyDoc_STRVAR(illuminantDoc, "get the  colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data");
/**
 @brief get the colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data
 @return tuple of the colorspace in which colorimetric results will be returned and the illuminant that will be used to convert spectral data to colorimetric data
 */
static
PyObject*
illuminant(PyObject* self, PyObject* args)
{
    const char* meterName;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
			    "Can't parse meterName option to i1ProAdapterModule illuminant");
    }
    iPAIlluminant_t illuminant;
    if (iPAGetIlluminant(meterName, &illuminant))
    {
        char* illuminantName;
        if (illuminantNameForIlluminant(illuminant, &illuminantName))
        {
            return Py_BuildValue("s", illuminantName);
        }
        else
        {
            return PyErr_Format(PyExc_IOError, "unable to recognize illuminant");
        }
    }
    else
    {
        return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
    }
}

PyDoc_STRVAR(setColorSpaceDoc, "set the colorspace in which colorimetric results will be returned");
/**
 @brief set the colorspace in which colorimetric results will be returned
 @return None
 */
static
PyObject*
setColorSpace(PyObject* self, PyObject* args)
{
    const char* meterName;
    const char* colorSpaceName;
    if (! PyArg_ParseTuple(args, "ss", &meterName, &colorSpaceName))
    {
        return PyErr_Format(PyExc_IOError, "unable to parse meterName and/or `colorSpace' argument");
    }
    // flushingFprintf(stdout, "colorSpaceName is `%s'\n", colorSpaceName);
    iPAColorSpace_t colorSpace;
    if (colorSpaceForColorSpaceName(colorSpaceName, &colorSpace))
    {
        // flushingFprintf(stdout, "about to call iiPASetMeasurementColorSpace(%d)\n", colorSpace);
        if (iPASetColorSpace(meterName, colorSpace))
        {
            return Py_None;
        }
        else
        {
            flushingFprintf(stdout, "iPASetMeasurementColorSpace did NOT return true\n");
            return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception,
                                "unable to set measurement color space");
        }
    }
    else
    {
        return PyErr_Format(PyExc_ValueError, "unable to recognize colorspace `%s'", colorSpace);
    }
}

PyDoc_STRVAR(setIlluminantDoc, "set the colorspace in which colorimetric results will be "
                               "returned and the illuminant that will be used to convert "
                               "spectral data to colorimetric data");

/**
 @brief set the illuminant that will be used to convert spectral data to colorimetric data
 @return None
 */
static
PyObject*
setIlluminant(PyObject* self, PyObject* args)
{
    const char* meterName;
    const char* illuminantName;
    if (! PyArg_ParseTuple(args, "ss", &meterName, &illuminantName))
    {
        return PyErr_Format(PyExc_IOError, "unable to parse meterName and/or 'illuminant' argument");
    }
    iPAIlluminant_t illuminant;
    if (illuminantForIlluminantName(illuminantName, &illuminant))
    {
        if (iPASetIlluminant(meterName, illuminant))
        {
            return Py_None;
        }
        else
        {
            return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception,
                                "unable to set measurement illuminant");
        }
    }
    else
    {
        return PyErr_Format(PyExc_ValueError, "unable to recognize illuminant `%s'", illuminant);
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
    const char* meterName;
    float tristimulus[3];
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
        "Can't parse meterName option to i1ProAdapterModule measuredColorimetry");
    }
    if (iPAGetColorimetry(meterName, tristimulus))
    {
        return Py_BuildValue("(fff)", tristimulus[0], tristimulus[1], tristimulus[2]);
    }
    assembleErrorText();
    return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception,
                        "%s (reading measured colorimetry)", assembledErrorTextBuffer);
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
    const char* meterName;
    const size_t spectrumSize = 36;
    float spectrum[spectrumSize];
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
        "Can't parse meterName option to i1ProAdapterModule measuredSpectrum");
    }
    if (iPAGetSpectrum(meterName, spectrum))
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
    return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception,
                        "%s (reading measured spectrum)", assembledErrorTextBuffer);
}

PyDoc_STRVAR(closeConnectionDoc, "close connection to meter");
static
PyObject*
closeConnection(PyObject* self, PyObject* args)
{
    const char* meterName;
    if (! PyArg_ParseTuple(args, "s", &meterName))
    {
        return PyErr_Format(PyExc_ValueError,
        "Can't parse meterName option to i1ProAdapterModule closeConnection");
    }
    if (iPAClose(meterName))
    {
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(meterNotFound() ? PyExc_LookupError : PyExc_Exception, "%s", assembledErrorTextBuffer);
}

static PyMethodDef i1ProAdapterFuncs[] = {
    {"setLogOptions",              (PyCFunction)setLogOptions,              METH_VARARGS, setLogOptionsDoc},
    {"sdkVersion",                 (PyCFunction)sdkVersion,                 METH_VARARGS, sdkVersionDoc},
    {"adapterVersion",             (PyCFunction)adapterVersion,             METH_NOARGS,  adapterVersionDoc},
    {"adapterModuleVersion",       (PyCFunction)adapterModuleVersion,       METH_NOARGS,  adapterModuleVersionDoc},
    {"meterID",                    (PyCFunction)meterId,                    METH_VARARGS, meterIdDoc},
    {"spectralRange",              (PyCFunction)spectralRange,              METH_VARARGS,  spectralRangeDoc},
    {"spectralResolution",         (PyCFunction)spectralResolution,         METH_VARARGS,  spectralResolutionDoc},
    {"populateRegistries",         (PyCFunction)populateRegistries,         METH_NOARGS,  populateRegistriesDoc},
    {"meterNamesAndModels",        (PyCFunction)meterNamesAndModels,        METH_NOARGS,  meterNamesAndModelsDoc},
    {"measurementModes",           (PyCFunction)measurementModes,           METH_NOARGS,  measurementModesDoc},
    {"measurementMode",            (PyCFunction)measurementMode,            METH_VARARGS, measurementModeDoc},
    {"setObserver",                (PyCFunction)setObserver,                METH_VARARGS, setObserverDoc},
    {"observers",                  (PyCFunction)observers,                  METH_NOARGS,  observersDoc},
    {"observer",                   (PyCFunction)observer,                   METH_VARARGS, observerDoc},
    {"setMeasurementMode",         (PyCFunction)setMeasurementMode,         METH_VARARGS, setMeasurementModeDoc},
    {"calibrate",                  (PyCFunction)calibrate,                  METH_VARARGS, calibrateDoc},
    {"trigger",                    (PyCFunction)trigger,                    METH_VARARGS, triggerDoc},
    {"getCalibrationTimes",        (PyCFunction)getCaliibrationTimes,       METH_VARARGS, getCalibrationTimesDoc},
    {"colorSpaces",                (PyCFunction)colorSpaces,                METH_NOARGS,  colorSpacesDoc},
    {"illuminants",                (PyCFunction)illuminants,                METH_NOARGS,  illuminantsDoc},
    {"colorSpace",                 (PyCFunction)colorSpace,                 METH_VARARGS, colorSpaceDoc},
    {"illuminant",                 (PyCFunction)illuminant,                 METH_VARARGS, illuminantDoc},
    {"setColorSpace",              (PyCFunction)setColorSpace,              METH_VARARGS, setColorSpaceDoc},
    {"setIlluminant",              (PyCFunction)setIlluminant,              METH_VARARGS, setIlluminantDoc},
    {"illuminants",                (PyCFunction)illuminants,                METH_NOARGS,  illuminantsDoc},
    {"measuredColorimetry",        (PyCFunction)measuredColorimetry,        METH_VARARGS, measuredColorimetryDoc},
    {"measuredSpectrum",           (PyCFunction)measuredSpectrum,           METH_VARARGS, measuredSpectrumDoc},
    {"closeConnection",            (PyCFunction)closeConnection,            METH_VARARGS, closeConnectionDoc},
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

