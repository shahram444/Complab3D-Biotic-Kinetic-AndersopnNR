// Minimal shim providing the plb::plint type so kinetics headers can compile
// without the full Palabos library.
#ifndef PLB_SHIM_H
#define PLB_SHIM_H

#include <cstdint>

namespace plb {
    typedef std::int64_t plint;
}

#endif // PLB_SHIM_H
