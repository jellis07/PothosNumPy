// Copyright (c) 2019 Nicholas Corgan
// SPDX-License-Identifier: GPL-3.0-or-later

#include "SimpleBlockTest.hpp"
#include "TestUtility.hpp"

#include <Pothos/Testing.hpp>
#include <Pothos/Framework.hpp>
#include <Pothos/Plugin.hpp>
#include <Pothos/Proxy.hpp>

#include <Poco/Thread.h>

#include <algorithm>
#include <cmath>
#include <complex>
#include <functional>
#include <string>
#include <typeinfo>

using SourceTestFunction = std::function<void(const Pothos::BufferChunk&)>;

//
// Common tests
//

template <typename T>
static void testAllValuesEqual(
    const Pothos::BufferChunk& bufferChunk,
    T testValue)
{
    const T* buffer = bufferChunk.as<const T*>();
    const size_t bufferLen = bufferChunk.elements();
    POTHOS_TEST_TRUE(bufferLen > 0);

    for(size_t i = 0; i < bufferLen; ++i)
    {
        testEqual(testValue, buffer[i]);
    }
}

//
// Test code
//

static void testSingleOutputSource(
    const Pothos::Proxy& testSource,
    const Pothos::DType& dtype,
    const SourceTestFunction& testFunction,
    bool forceEnd)
{
    auto collector = Pothos::BlockRegistry::make(
                         "/blocks/collector_sink",
                         dtype);

    // Run the topology
    {
        Pothos::Topology topology;
        topology.connect(testSource, 0, collector, 0);
        topology.commit();

        if(forceEnd)
        {
            // When this block exits, the flowgraph will stop.
            Poco::Thread::sleep(10);
        }
        else
        {
            POTHOS_TEST_TRUE(topology.waitInactive(0.01));
        }
    }

    testFunction(collector.call("getBuffer"));
}

template <typename T>
static void testOnes()
{
    using std::placeholders::_1;

    constexpr size_t dimension = 1;
    Pothos::DType dtype(typeid(T), dimension);
    std::cout << "Testing " << dtype.toString() << std::endl;

    auto ones = Pothos::BlockRegistry::make(
                    "/numpy/ones",
                    dtype);

    testSingleOutputSource(
        ones,
        dtype,
        std::bind(testAllValuesEqual<T>, _1, T(1)),
        true);
}

template <typename T>
static void testZeros()
{
    using std::placeholders::_1;

    constexpr size_t dimension = 1;
    Pothos::DType dtype(typeid(T), dimension);
    std::cout << "Testing " << dtype.toString() << std::endl;

    auto zeros = Pothos::BlockRegistry::make(
                     "/numpy/zeros",
                    dtype);
 
    testSingleOutputSource(
        zeros,
        dtype,
        std::bind(testAllValuesEqual<T>, _1, T(0)),
        true);
}

template <typename T>
static inline EnableIfComplex<T, T> getFullFillValue()
{
    using S = typename T::value_type;

    return T{S(10),S(20)};
}

template <typename T>
static inline EnableIfNotComplex<T, T> getFullFillValue()
{
    return T(5);
}

template <typename T>
static void testFull()
{
    using std::placeholders::_1;

    constexpr size_t dimension = 1;
    Pothos::DType dtype(typeid(T), dimension);
    std::cout << "Testing " << dtype.toString() << std::endl;

    auto full = Pothos::BlockRegistry::make(
                     "/numpy/full",
                    dtype,
                    getFullFillValue<T>());

    const T testValue1 = getFullFillValue<T>();
    const T testValue2 = testValue1 + T(1);

    // Check the initial value.
    testEqual(
        testValue1,
        full.template call<T>("getFillValue"));

    testSingleOutputSource(
        full,
        dtype,
        std::bind(testAllValuesEqual<T>, _1, testValue1),
        true);

    // Set the value, test it, and try again with the new value.
    full.call("setFillValue", testValue2);
    testEqual(
        testValue2,
        full.template call<T>("getFillValue"));

    testSingleOutputSource(
        full,
        dtype,
        std::bind(testAllValuesEqual<T>, _1, testValue2),
        true);
}

//
// Registered tests
//

POTHOS_TEST_BLOCK("/numpy/tests", test_ones)
{
    testOnes<std::int8_t>();
    testOnes<std::int16_t>();
    testOnes<std::int32_t>();
    testOnes<std::int64_t>();
    testOnes<std::uint8_t>();
    testOnes<std::uint16_t>();
    testOnes<std::uint32_t>();
    testOnes<std::uint64_t>();
    testOnes<float>();
    testOnes<double>();
    testOnes<std::complex<float>>();
    testOnes<std::complex<double>>();
}

POTHOS_TEST_BLOCK("/numpy/tests", test_zeros)
{
    testZeros<std::int8_t>();
    testZeros<std::int16_t>();
    testZeros<std::int32_t>();
    testZeros<std::int64_t>();
    testZeros<std::uint8_t>();
    testZeros<std::uint16_t>();
    testZeros<std::uint32_t>();
    testZeros<std::uint64_t>();
    testZeros<float>();
    testZeros<double>();
    testZeros<std::complex<float>>();
    testZeros<std::complex<double>>();
}

POTHOS_TEST_BLOCK("/numpy/tests", test_full)
{
    testFull<std::int8_t>();
    testFull<std::int16_t>();
    testFull<std::int32_t>();
    testFull<std::int64_t>();
    testFull<std::uint8_t>();
    testFull<std::uint16_t>();
    testFull<std::uint32_t>();
    testFull<std::uint64_t>();
    testFull<float>();
    testFull<double>();
    testFull<std::complex<float>>();
    testFull<std::complex<double>>();
}