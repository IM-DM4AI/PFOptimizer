#include <Python.h>
#include <chrono>
#include <iostream>

int main() {
    Py_Initialize(); 

    // pre-import the inference context reuse cache once before iterative UDF invocation (e.g. plan time)
    PyObject *dycacher = PyImport_ImportModule("dycacher");
    if (!dycacher) {
        PyErr_Print();
    }

    // load udf code, construct call object
    PyObject *sys = PyImport_ImportModule("sys");
    PyObject *path = PyObject_GetAttrString(sys,"path");
    PyList_Append(path,PyUnicode_FromString(".."));
    PyObject *pModule = PyImport_ImportModule("udf_code");
    if(!pModule){
        PyErr_Print();
        printf("ERROR:failed to load udf_code.py\n");
    }
    PyObject *pFunc = PyObject_GetAttrString(pModule,"predict");
    if(!pFunc || !PyCallable_Check(pFunc))
    {
        PyErr_Print();
        printf("ERROR:function predict not found or not callable\n");
        return 1;
    }


    // simulate the iterative process of UDF invocation
    PyObject *pValue;

    auto start = std::chrono::steady_clock::now();
    for(int i = 0; i < 10000; i++) {
        pValue = PyObject_CallObject(pFunc,NULL);
        if(!pValue)
        {
            PyErr_Print();
            printf("ERROR: function call failed\n");
            return 1;
        }
        Py_DECREF(pValue);
    }
    auto stop = std::chrono::steady_clock::now();

    double duration = std::chrono::duration<double, std::milli>(stop - start).count();

    std::cout<< duration <<"ms"<<std::endl;

    Py_DECREF(pFunc);
    Py_DECREF(pModule);
    // Py_DECREF(dycacher);


    Py_Finalize();
    return 0;
}