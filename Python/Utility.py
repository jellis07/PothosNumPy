# Copyright (c) 2019 Nicholas Corgan
# SPDX-License-Identifier: BSD-3-Clause

import Pothos

import numpy

def DType(*args):
    env = Pothos.ProxyEnvironment("managed")
    reg = env.findProxy("Pothos/DType")
    return reg(*args)

# Strings can be passed in for the DType parameters.
def toDType(dtypeInput):
    if type(dtypeInput) is str:
        return DType(dtypeInput)
    elif type(dtypeInput) is Pothos.Proxy:
        return dtypeInput
    else:
        raise TypeError("Invalid input: {0}".format(type(dtypeInput)))

# Pothos supports all complex types, but NumPy does not support
# complex integral types, so we must catch this on block instantiation.
# Also confirm that the given DType is 1-dimensional, as that is all
# these blocks support.
def validateDType(dtype, dtypeArgs):
    typeStr = dtype.toString()
    if ("complex_u" in typeStr) or ("complex_i" in typeStr) or dtype.isCustom():
        raise TypeError("NumPy does not support type {0}".format(typeStr))

    if dtype.dimension() > 1:
        raise TypeError("PothosNumPy only supports DTypes of dimension 1.")

    if dtypeArgs.get("supportAll", False):
        return

    UNSUPPORTED_TEMPLATE = "{0} types are not supported."
    unsupportedType = None

    if dtype.isSigned() and not dtypeArgs.get("supportInt", False):
        unsupportedType = "int"
    elif (dtype.isInteger() and not dtype.isSigned()) and not dtypeArgs.get("supportUInt", False):
        unsupportedType = "uint"
    elif (dtype.isFloat() and not dtype.isComplex()) and not dtypeArgs.get("supportFloat", False):
        unsupportedType = "float"
    elif dtype.isComplex() and not dtypeArgs.get("supportComplex", False):
        unsupportedType = "complex"

    if unsupportedType is not None:
        raise TypeError(UNSUPPORTED_TEMPLATE.format(unsupportedType))

def dtypeToComplex(dtype, errorIfAlreadyComplex=False):
    if dtype.isComplex():
        if errorIfAlreadyComplex:
            raise TypeError("The given DType ({0}) is already complex.".format(dtype.name()))
        else:
            return dtype

    return DType("complex_"+dtype.name())

def dtypeToScalar(dtype, errorIfAlreadyScalar=False):
    if not dtype.isComplex():
        if errorIfAlreadyScalar:
            raise TypeError("The given DType ({0}) is already scalar.".format(dtype.name()))
        else:
            return dtype

    return DType(dtype.name().replace("complex_",""))

def validateComplexParamRange(param, blockDType):
    VALUE_ERROR_TEMPLATE = "{0} part of given value {1} is outside the valid {2} range [{3}, {4}]."

    scalarDType = numpy.dtype("double") if ("complex128" == blockDType.name) else numpy.dtype("float")

    finfo = numpy.finfo(scalarDType)
    minValue = finfo.min
    maxValue = finfo.max

    if (param.real < minValue) or (param.real > maxValue):
        raise ValueError(VALUE_ERROR_TEMPLATE.format("Real", param.real, blockDType.name, minValue, maxValue))
    if (param.imag < minValue) or (param.imag > maxValue):
        raise ValueError(VALUE_ERROR_TEMPLATE.format("Imaginary", param.imag, blockDType.name, minValue, maxValue))

def validateScalarParamRange(param, blockDType):
    VALUE_ERROR_TEMPLATE = "Given value {0} is outside the valid {1} range [{2}, {3}]."
    minValue = None
    maxValue = None
    if type(param) == float:
        finfo = numpy.finfo(blockDType)
        minValue = finfo.min
        maxValue = finfo.max
    elif type(param) == int:
        iinfo = numpy.iinfo(blockDType)
        minValue = iinfo.min
        maxValue = iinfo.max

    if (param < minValue) or (param > maxValue):
        raise ValueError(VALUE_ERROR_TEMPLATE.format(param, blockDType.name, minValue, maxValue))

# Since Python is not strongly typed, we need this to make sure callers can't
# change variable types after the fact.
def validateParameter(param, blockDType):
    TYPE_ERROR_TEMPLATE = "Given value {0} is of type {1}, which is incompatible with parameter type {2}."

    # Make sure we're checking the actual scalar type, since blockDType may
    # describe an array type.
    if blockDType.subdtype is not None:
        blockDType = blockDType.subdtype[0]

    if type(param) == float:
        if blockDType.kind != "f":
            raise TypeError(TYPE_ERROR_TEMPLATE.format(param, type(param), blockDType.name))

    paramDType = numpy.dtype(type(param))

    if paramDType.kind in "iu":
        if blockDType.kind == "f":
            # Avoids creating invalid iinfo/finfo
            param = float(param)
        elif blockDType.kind not in "iu":
            raise TypeError(TYPE_ERROR_TEMPLATE.format(param, type(param), blockDType.name))
    if ("complex" in paramDType.name) != ("complex" in blockDType.name):
        raise TypeError(TYPE_ERROR_TEMPLATE.format(param, type(param), blockDType.name))

    # Now that we know that both types are either floating-point or integral, make
    # sure the input value will fit in the block type.
    if "complex" in paramDType.name:
        validateComplexParamRange(param, blockDType)
    else:
        validateScalarParamRange(param, blockDType)

def errorForUnevenIntegralSpace(func, start, stop, numValues, numpyDType):
    if (type(start) is int) and (type(stop) is int) and (type(numValues) is int):
        output = func(start, stop, numValues)
        areAnyFloat = not all(numpy.float32(numpyDType.type(output)) == numpy.float32(output))
        if areAnyFloat:
            ERROR_FORMAT = "The parameters start={0}, stop={1}, numValues={2} " \
                           "resulted in non-integral values, which cannot be " \
                           "represented with DType {3}."
            errorString = ERROR_FORMAT.format(start, stop, numValues, numpyDType.name)
            raise ValueError(errorString)

def errorForLeftGERight(left, right):
    if (type(left) in [int, float]) and (type(right) in [int, float]) and (left >= right):
        raise ValueError("{0} >= {1}".format(left, right))
