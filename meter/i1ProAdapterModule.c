//
//  i1ProAdapterModule.c
//  i1ProAdapterModule
//
//  Created by Joseph Goldstone on 5/26/19.
//  Copyright © 2019 Arnold & Richter Cine Technik. All rights reserved.
//

#include "i1ProAdapter.h"
#include <Python.h>

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

PyDoc_STRVAR(moduleVersionDoc, "get version of Python i1ProAdapter extension");
const static uint16_t moduleVersionMajor = 0;
const static uint16_t moduleVersionMinor = 1;
const static uint16_t moduleVersionEdit = 0;
const char* build = "pre-alpha";

#define ASSEMBLED_MODULE_VERSION_LENGTH 256
const size_t assembledModuleVersionLength = ASSEMBLED_MODULE_VERSION_LENGTH;
static char assembledModuleVersionBuffer[assembledModuleVersionLength];

static
PyObject*
moduleVersion(PyObject* self, PyObject* args)
{
    bzero(assembledModuleVersionBuffer, assembledModuleVersionLength);
    if (strlen(build) == 0)
    {
        snprintf(assembledModuleVersionBuffer, assembledModuleVersionLength, "%d.%d.%d", moduleVersionMajor, moduleVersionMinor, moduleVersionEdit);
    } else {
        snprintf(assembledModuleVersionBuffer, assembledModuleVersionLength, "%d.%d.%d (%s)", moduleVersionMajor, moduleVersionMinor, moduleVersionEdit, build);
    }
    return Py_BuildValue("s", assembledModuleVersionBuffer);
}

PyDoc_STRVAR(adapterVersionDoc, "get version of i1ProAdapter");

#define ASSEMBLED_ADAPTER_VERSION_LENGTH 256
const size_t assembledAdapterVersionLength = ASSEMBLED_ADAPTER_VERSION_LENGTH;
static char assembledAdapterVersionBuffer[assembledAdapterVersionLength];

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

PyDoc_STRVAR(attachDoc, "attach to meter");
/**
 @brief attach to an i1Pro meter
 @return None if no error; throws PyExc_IOError if any error
 */
static
PyObject*
attach(PyObject* self)
{
    bool attachResult = iPAAttach();
    if (attachResult)
    {
        return Py_None;
    }
    assembleErrorText();
    return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
}

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
    PyArg_ParseTuple(args, "p", &predicate);
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

//static
//PyObject*
//lastCalibrationTime(PyObject* self, PyObject* args)
//{
//    PyObject* result = NULL;
//    // TODO: write body that assembles a tuple of tuples of mode and time strings, e.g. ( ( "emissive", "..." ), ( "ambient", "never" ), ( "reflective", "never" ) )
//    return result;
//}

//static
//PyObject*
//activeMeasurementMode(PyObject* self, PyObject* args)
//{
//    PyObject* result = NULL;
//    // TODO: write body that calls i1_GetOption to get current measurement mode
//    return result;
//}

//static
//PyObject*
//measurementModes(PyObject* self, PyObject* args)
//{
//    PyObject* result = NULL;
//    // TODO: write body that assembles a tuple of strings of modes, e.g. ( "emissive", "ambient", "reflective" )
//    return result;
//}

PyDoc_STRVAR(setMeasurementModeDoc, "set measurement mode to one of 'emissive' or 'reflective'");

static
PyObject*
setMeasurementMode(PyObject* self, PyObject* args)
{
    const char* mode;
    if (! PyArg_ParseTuple(args, "s", &mode))
    {
        return PyErr_Format(PyExc_IOError, "Unknown measurement mode '%s'; known modes are 'emissive' and 'reflective'", mode);
    }
    if (strcmp(mode, "emissive") == 0)
    {
        if (iPASetMeasurementMode(I1PRO_EMISSIVE_MEASUREMENT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
        }
    }
    else if (strcmp(mode, "reflective") == 0)
    {
        if (iPASetMeasurementMode(I1PRO_REFLECTIVE_MEASUREMENT))
        {
            return Py_None;
        } else {
            assembleErrorText();
            return PyErr_Format(PyExc_IOError, "%s", assembledErrorTextBuffer);
        }
    }
    return PyErr_Format(PyExc_IOError, "Unknown measurement mode '%s'; known modes are 'emissive' and 'reflective'", mode);
}

PyDoc_STRVAR(triggerDoc, "trigger a measurement");
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

//static
//PyObject*
//colorspaces(PyObject* self)
//{
//    PyObject* result = NULL;
//    // TODO: write body that assembles a tuple of strings of modes, e.g. ( "emissive", "ambient", "reflective" )
//    return result;
//}

//static
//PyObject*
//currentColorspace(PyObject* self, PyObject* args)
//{
//    PyObject* result = NULL;
//    // TODO: write body that uses i1_GetOption() to retrive the current colorspace
//    return result;
//}

//static
//PyObject*
//setCurrentColorspace(PyObject* self, PyObject* args)
//{
//    PyObject* result = NULL;
//    // TODO: write body that sets the current colorspace
//    return result;
//}


PyDoc_STRVAR(measuredColorimetryDoc, "read colorimetry from a triggered measurement");
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
    {"sdkVersion",                (PyCFunction)sdkVersion,                METH_NOARGS,  sdkVersionDoc},
    {"moduleVersion",             (PyCFunction)moduleVersion,             METH_NOARGS,  moduleVersionDoc},
    {"adapterVersion",            (PyCFunction)adapterVersion,            METH_NOARGS,  adapterVersionDoc},
    {"attach",                     (PyCFunction)attach,                    METH_NOARGS,  attachDoc},
    {"openConnection",                       (PyCFunction)openConnection,                      METH_VARARGS, openConnectionDoc},
    {"meterID",                    (PyCFunction)meterId,                   METH_NOARGS,  meterIdDoc},
    {"spectralRange",              (PyCFunction)spectralRange,            METH_NOARGS,  spectralRangeDoc},
    {"spectralResolution",        (PyCFunction)spectralResolution,        METH_NOARGS,  spectralResolutionDoc},
    {"setMeasurementMode",        (PyCFunction)setMeasurementMode,        METH_VARARGS, setMeasurementModeDoc},
    {"trigger",                    (PyCFunction)trigger,                   METH_NOARGS,  triggerDoc},
    {"measuredColorimetry",       (PyCFunction)measuredColorimetry,       METH_NOARGS,  measuredColorimetryDoc},
    {"measuredSpectrum", (PyCFunction)measuredSpectrum, METH_NOARGS,  measuredSpectrumDoc},
    {"closeConnection", (PyCFunction)closeConnection, METH_VARARGS, closeConnectionDoc},
    {"detach", (PyCFunction)detach, METH_NOARGS, detachDoc},
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

