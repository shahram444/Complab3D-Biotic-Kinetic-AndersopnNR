/* This file is a part of the CompLaB program.
 *
 * The CompLaB softare is developed since 2022 by the University of Georgia
 * (United States) and Chungnam National University (South Korea).
 * 
 * Contact:
 * Heewon Jung
 * Department of Geological Sciences 
 * Chungnam National University
 * 99 Daehak-ro, Yuseong-gu
 * Daejeon 34134, South Korea
 * hjung@cnu.ac.kr
 *
 * The most recent release of CompLaB can be downloaded at 
 * https://bitbucket.org/MeileLab/complab/downloads/
 *
 * CompLaB is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * The library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef COMPLAB3D_PROCESSORS_PART4_HH
#define COMPLAB3D_PROCESSORS_PART4_HH

#include <cmath>
#include <limits>
#include <vector>
#include <string>
#include <algorithm>
#include <iomanip>

using namespace plb;
typedef double T;

/* ===============================================================================================================
   ==================== ANDERSON ACCELERATION + PCF EQUILIBRIUM SOLVER ==========================================
   ===============================================================================================================
 * 
 * REFERENCES:
 * [1] Anderson (1965) - Original Anderson Acceleration
 * [2] Walker & Ni (2011) - Convergence analysis, condition monitoring
 * [3] Carrayrou et al. (2002) - PCF method for equilibrium chemistry
 * [4] Awada et al. (2025) - Anderson + PCF combination, 99.5% convergence
 * 
 * USAGE:
 *   This solver handles fast equilibrium reactions (e.g., carbonate chemistry)
 *   that equilibrate much faster than transport/kinetics timescales.
 *   
 *   Operator Splitting Approach:
 *   1. Transport (LBM advection-diffusion)
 *   2. Kinetics (run_kinetics - microbial reactions)  
 *   3. Equilibrium (run_equilibrium_biotic - fast abiotic reactions)
 *
 * =============================================================================================================== */

template<typename T>
class EquilibriumChemistry 
{
public:
    // Physical bounds for concentrations
    static constexpr T MIN_CONC = 1e-30;
    static constexpr T MAX_CONC = 10.0;
    static constexpr T MIN_LOG_C = -30.0;
    static constexpr T MAX_LOG_C = 1.0;
    
    // Default solver parameters
    static constexpr plint DEFAULT_ANDERSON_DEPTH = 4;
    static constexpr T DEFAULT_CONDITION_TOL = 1e10;
    static constexpr T DEFAULT_BETA = 1.0;
    
    EquilibriumChemistry() 
        : maxIterations(200), tolerance(1e-8), lastConverged(true),   // Relaxed tolerance for better convergence
          lastIterations(0), lastResidual(0.0), verbose(false),
          totalSolves(0), totalConverged(0), totalDiverged(0),
          andersonDepth(DEFAULT_ANDERSON_DEPTH), 
          conditionTol(DEFAULT_CONDITION_TOL), beta(DEFAULT_BETA) {}
    
    /* ============================= SETTERS ============================= */
    
    void setSpeciesNames(const std::vector<std::string>& names) {
        species_names.clear();
        for (const auto& name : names) {
            if (name != "H2O" && name != "h2o") species_names.push_back(name);
        }
    }
    
    void setComponentNames(const std::vector<std::string>& names) { 
        component_names = names; 
    }
    
    void setLogK(const std::vector<T>& logK) { 
        logK_values = logK; 
    }
    
    void setStoichiometryMatrix(const std::vector<std::vector<T>>& S) { 
        stoich_matrix = S; 
    }
    
    void setMaxIterations(plint maxIter) { 
        maxIterations = maxIter; 
    }
    
    void setTolerance(T tol) { 
        tolerance = tol; 
    }
    
    void setVerbose(bool v) { 
        verbose = v; 
    }
    
    void setAndersonDepth(plint depth) { 
        andersonDepth = std::max(plint(1), depth); 
    }
    
    void setConditionTolerance(T condTol) { 
        conditionTol = condTol; 
    }
    
    void setBeta(T betaVal) { 
        beta = betaVal; 
    }
    
    /* ============================= GETTERS ============================= */
    
    plint getMaxIterations() const { return maxIterations; }
    T getTolerance() const { return tolerance; }
    std::vector<T> getLogK() const { return logK_values; }
    bool didConverge() const { return lastConverged; }
    std::vector<std::string> getSpeciesNames() const { return species_names; }
    std::vector<std::string> getComponentNames() const { return component_names; }
    plint getNumSpecies() const { return species_names.size(); }
    plint getNumComponents() const { return component_names.size(); }
    plint getLastIterations() const { return lastIterations; }
    T getLastResidual() const { return lastResidual; }
    plint getAndersonDepth() const { return andersonDepth; }
    plint getTotalSolves() const { return totalSolves; }
    plint getTotalConverged() const { return totalConverged; }
    plint getTotalDiverged() const { return totalDiverged; }
    
    void resetStatistics() { 
        totalSolves = totalConverged = totalDiverged = 0; 
    }
    
    /* ============================= SPECIES HANDLING ============================= */
    
    // Check if species participates in equilibrium (has non-zero stoichiometry)
    bool isEquilibriumSpecies(size_t species_idx) const {
        if (species_idx >= stoich_matrix.size()) return false;
        for (size_t j = 0; j < stoich_matrix[species_idx].size(); ++j) {
            if (std::abs(stoich_matrix[species_idx][j]) > 1e-10) return true;
        }
        return false;
    }
    
    void setStoichiometryRow(size_t species_idx, const std::vector<T>& row) {
        if (species_idx < stoich_matrix.size() && row.size() == component_names.size()) {
            stoich_matrix[species_idx] = row;
        }
    }
    
    /* ============================= MASS ACTION CALCULATIONS ============================= */
    
    // Calculate species concentrations from component log-concentrations
    // Mass action: [C_i] = 10^(logK[i] + sum_j S[i][j]*logC[j])
    std::vector<T> calc_species(const std::vector<T>& logC, 
                                const std::vector<T>& initial_conc = std::vector<T>()) const {
        size_t ns = species_names.size();
        size_t nc = component_names.size();
        std::vector<T> conc(ns);
        
        for (size_t i = 0; i < ns; ++i) {
            // Non-equilibrium species: preserve initial concentration
            if (!isEquilibriumSpecies(i)) {
                conc[i] = (i < initial_conc.size() && initial_conc[i] > MIN_CONC) 
                          ? std::min(initial_conc[i], MAX_CONC) : MIN_CONC;
                continue;
            }
            
            // Equilibrium species: apply mass action law
            T logConc = (i < logK_values.size()) ? logK_values[i] : 0.0;
            for (size_t j = 0; j < nc; ++j) {
                if (j < stoich_matrix[i].size()) {
                    logConc += stoich_matrix[i][j] * logC[j];
                }
            }
            
            // Bound and convert from log
            logConc = std::max(std::min(logConc, MAX_LOG_C), MIN_LOG_C);
            conc[i] = std::pow(10.0, logConc);
            
            // Handle numerical issues
            if (std::isnan(conc[i]) || std::isinf(conc[i])) {
                conc[i] = (i < initial_conc.size() && initial_conc[i] > MIN_CONC) 
                          ? initial_conc[i] : MIN_CONC;
            }
            conc[i] = std::max(std::min(conc[i], MAX_CONC), MIN_CONC);
        }
        return conc;
    }
    
    // Calculate component totals: T_j = sum_i S[i][j] * [C_i]
    std::vector<T> calc_component_totals(const std::vector<T>& species_conc) const {
        size_t nc = component_names.size();
        size_t ns = species_names.size();
        std::vector<T> T_total(nc, 0.0);
        
        for (size_t j = 0; j < nc; ++j) {
            for (size_t i = 0; i < ns && i < species_conc.size(); ++i) {
                if (isEquilibriumSpecies(i) && j < stoich_matrix[i].size()) {
                    T conc_safe = std::max(std::min(species_conc[i], MAX_CONC), MIN_CONC);
                    T_total[j] += stoich_matrix[i][j] * conc_safe;
                }
            }
            T_total[j] = std::max(T_total[j], MIN_CONC);
        }
        return T_total;
    }
    
    /* ============================= PCF METHOD [Carrayrou et al. 2002] ============================= */
    
    // Calculate reactive and product sums for PCF iteration
    std::pair<std::vector<T>, std::vector<T>> calc_reactive_product_sums(
            const std::vector<T>& species_conc, const std::vector<T>& T_total) const {
        size_t nc = component_names.size();
        size_t ns = species_names.size();
        std::vector<T> S_reactive(nc, 0.0), S_product(nc, 0.0);
        
        for (size_t j = 0; j < nc; ++j) {
            T sum_positive = 0.0, sum_negative = 0.0;
            
            for (size_t i = 0; i < ns && i < species_conc.size(); ++i) {
                if (!isEquilibriumSpecies(i) || j >= stoich_matrix[i].size()) continue;
                
                T mu_ij = stoich_matrix[i][j];
                T c_i = std::max(species_conc[i], MIN_CONC);
                
                if (mu_ij > 1e-15) {
                    sum_positive += mu_ij * c_i;
                } else if (mu_ij < -1e-15) {
                    sum_negative += std::abs(mu_ij) * c_i;
                }
            }
            
            if (T_total[j] >= 0.0) {
                S_reactive[j] = sum_positive;
                S_product[j] = T_total[j] + sum_negative;
            } else {
                S_reactive[j] = std::abs(T_total[j]) + sum_positive;
                S_product[j] = sum_negative;
            }
            
            S_reactive[j] = std::max(S_reactive[j], MIN_CONC);
            S_product[j] = std::max(S_product[j], MIN_CONC);
        }
        return std::make_pair(S_reactive, S_product);
    }
    
    // PCF residual: f(w) = G(w) - w
    std::vector<T> pcf_residual(const std::vector<T>& logC, const std::vector<T>& T_total,
                                const std::vector<T>& initial_conc) const {
        size_t nc = component_names.size();
        std::vector<T> species_conc = calc_species(logC, initial_conc);
        auto sums = calc_reactive_product_sums(species_conc, T_total);
        const std::vector<T>& S_R = sums.first;
        const std::vector<T>& S_P = sums.second;
        
        std::vector<T> f(nc);
        for (size_t j = 0; j < nc; ++j) {
            // Find minimum positive stoichiometry coefficient
            T mu_i0_j = 1.0;
            for (size_t i = 0; i < stoich_matrix.size(); ++i) {
                if (!isEquilibriumSpecies(i)) continue;
                if (j < stoich_matrix[i].size()) {
                    T mu = stoich_matrix[i][j];
                    if (mu > 1e-10 && mu < mu_i0_j) mu_i0_j = mu;
                }
            }
            
            f[j] = (1.0 / mu_i0_j) * (std::log10(S_P[j]) - std::log10(S_R[j]));
            f[j] = std::max(std::min(f[j], 10.0), -10.0);
            
            if (std::isnan(f[j]) || std::isinf(f[j])) f[j] = 0.0;
        }
        return f;
    }
    
    /* ============================= VECTOR OPERATIONS ============================= */
    
    T norm(const std::vector<T>& v) const {
        T s = 0; 
        for (T x : v) s += x * x; 
        return std::sqrt(s);
    }
    
    std::vector<T> vec_subtract(const std::vector<T>& a, const std::vector<T>& b) const {
        std::vector<T> r(a.size());
        for (size_t i = 0; i < a.size(); ++i) {
            r[i] = a[i] - (i < b.size() ? b[i] : 0.0);
        }
        return r;
    }
    
    std::vector<T> vec_add(const std::vector<T>& a, const std::vector<T>& b) const {
        std::vector<T> r(a.size());
        for (size_t i = 0; i < a.size(); ++i) {
            r[i] = a[i] + (i < b.size() ? b[i] : 0.0);
        }
        return r;
    }
    
    T dot_product(const std::vector<T>& a, const std::vector<T>& b) const {
        T sum = 0; 
        for (size_t i = 0; i < a.size() && i < b.size(); ++i) {
            sum += a[i] * b[i];
        }
        return sum;
    }
    
    /* ============================= QR DECOMPOSITION ============================= */
    
    // QR decomposition with condition number monitoring [Walker & Ni 2011]
    void qr_decomposition(const std::vector<std::vector<T>>& columns,
                          std::vector<std::vector<T>>& Q,
                          std::vector<std::vector<T>>& R, T& condNum) const {
        size_t m = columns.size();
        if (m == 0) { condNum = 1.0; return; }
        size_t n = columns[0].size();
        
        Q.resize(m); 
        R.resize(m, std::vector<T>(m, 0.0));
        T R_max = 0.0, R_min = std::numeric_limits<T>::max();
        
        for (size_t j = 0; j < m; ++j) {
            Q[j] = columns[j];
            
            // Gram-Schmidt orthogonalization
            for (size_t i = 0; i < j; ++i) {
                R[i][j] = dot_product(Q[i], columns[j]);
                for (size_t k = 0; k < n; ++k) {
                    Q[j][k] -= R[i][j] * Q[i][k];
                }
            }
            
            R[j][j] = norm(Q[j]);
            if (R[j][j] > 1e-15) {
                for (size_t k = 0; k < n; ++k) {
                    Q[j][k] /= R[j][j];
                }
            }
            
            // Track condition number
            T absR = std::abs(R[j][j]);
            if (absR > R_max) R_max = absR;
            if (absR > 1e-30 && absR < R_min) R_min = absR;
        }
        
        condNum = (R_min > 1e-30) ? R_max / R_min : std::numeric_limits<T>::max();
    }
    
    // Solve upper triangular system Rx = b
    std::vector<T> solve_upper_triangular(const std::vector<std::vector<T>>& R,
                                          const std::vector<T>& b) const {
        size_t m = R.size();
        std::vector<T> x(m, 0.0);
        
        for (int i = m - 1; i >= 0; --i) {
            x[i] = b[i];
            for (size_t j = i + 1; j < m; ++j) {
                x[i] -= R[i][j] * x[j];
            }
            if (std::abs(R[i][i]) > 1e-30) {
                x[i] /= R[i][i];
            }
        }
        return x;
    }
    
    /* ============================= MAIN SOLVER ============================= */
    
    // Anderson Acceleration solver for equilibrium chemistry
    std::vector<T> solve_equilibrium_anderson(const std::vector<T>& initial_species_conc,
                                              const std::vector<T>& T_total) {
        lastConverged = false;
        lastIterations = 0;
        lastResidual = 0.0;
        totalSolves++;
        
        size_t nc = component_names.size();
        if (nc == 0) { 
            lastConverged = true; 
            totalConverged++; 
            return initial_species_conc; 
        }
        
        // Initialize omega = log10([component])
        std::vector<T> omega(nc);
        for (size_t j = 0; j < nc; ++j) {
            auto it = std::find(species_names.begin(), species_names.end(), component_names[j]);
            T comp_conc = 1e-7;
            if (it != species_names.end()) {
                size_t idx = std::distance(species_names.begin(), it);
                if (idx < initial_species_conc.size()) {
                    comp_conc = initial_species_conc[idx];
                }
            }
            comp_conc = std::max(std::min(comp_conc, MAX_CONC), MIN_CONC);
            omega[j] = std::log10(comp_conc);
        }
        
        // First PCF step
        std::vector<T> f0 = pcf_residual(omega, T_total, initial_species_conc);
        std::vector<T> omega_new = vec_add(omega, f0);
        for (size_t j = 0; j < nc; ++j) {
            omega_new[j] = std::max(std::min(omega_new[j], MAX_LOG_C), MIN_LOG_C);
        }
        
        // History storage for Anderson Acceleration
        std::vector<std::vector<T>> omega_history, f_history;
        omega_history.push_back(omega);
        f_history.push_back(f0);
        omega = omega_new;
        
        // Main iteration loop
        for (plint iter = 1; iter < maxIterations; ++iter) {
            lastIterations = iter;
            
            std::vector<T> f_k = pcf_residual(omega, T_total, initial_species_conc);
            T f_norm = norm(f_k);
            lastResidual = f_norm;
            
            // Check convergence
            if (f_norm < tolerance) {
                lastConverged = true;
                totalConverged++;
                return calc_species(omega, initial_species_conc);
            }
            
            // Store history
            omega_history.push_back(omega);
            f_history.push_back(f_k);
            
            // Determine Anderson depth for this iteration
            plint m_k = std::min(andersonDepth, (plint)(f_history.size() - 1));
            
            if (m_k < 1) {
                // Simple fixed-point iteration
                omega_new = vec_add(omega, f_k);
            } else {
                // Anderson Acceleration
                std::vector<std::vector<T>> Delta_F, Delta_X;
                size_t hist_size = f_history.size();
                
                for (plint i = 0; i < m_k; ++i) {
                    size_t idx = hist_size - m_k - 1 + i;
                    Delta_F.push_back(vec_subtract(f_history[idx + 1], f_history[idx]));
                    Delta_X.push_back(vec_subtract(omega_history[idx + 1], omega_history[idx]));
                }
                
                // QR factorization with condition monitoring
                std::vector<std::vector<T>> Q, R;
                T condNum;
                qr_decomposition(Delta_F, Q, R, condNum);
                
                // Reduce depth if ill-conditioned
                while (condNum > conditionTol && Delta_F.size() > 1) {
                    Delta_F.erase(Delta_F.begin());
                    Delta_X.erase(Delta_X.begin());
                    qr_decomposition(Delta_F, Q, R, condNum);
                }
                
                // Solve least squares problem
                std::vector<T> Qt_fk(Delta_F.size());
                for (size_t i = 0; i < Delta_F.size(); ++i) {
                    Qt_fk[i] = dot_product(Q[i], f_k);
                }
                std::vector<T> gamma = solve_upper_triangular(R, Qt_fk);
                
                // Compute Anderson update
                std::vector<T> DX_gamma(nc, 0.0), DF_gamma(nc, 0.0);
                for (size_t i = 0; i < Delta_X.size() && i < gamma.size(); ++i) {
                    for (size_t j = 0; j < nc; ++j) {
                        DX_gamma[j] += Delta_X[i][j] * gamma[i];
                        DF_gamma[j] += Delta_F[i][j] * gamma[i];
                    }
                }
                
                omega_new.resize(nc);
                for (size_t j = 0; j < nc; ++j) {
                    omega_new[j] = omega[j] - DX_gamma[j] + beta * (f_k[j] - DF_gamma[j]);
                }
            }
            
            // Bound and validate new iterate
            for (size_t j = 0; j < nc; ++j) {
                omega_new[j] = std::max(std::min(omega_new[j], MAX_LOG_C), MIN_LOG_C);
                if (std::isnan(omega_new[j]) || std::isinf(omega_new[j])) {
                    omega_new[j] = omega[j];
                }
            }
            omega = omega_new;
            
            // Trim history to maintain memory efficiency
            while (omega_history.size() > (size_t)(andersonDepth + 1)) {
                omega_history.erase(omega_history.begin());
                f_history.erase(f_history.begin());
            }
        }
        
        // Did not converge within max iterations
        totalDiverged++;
        return calc_species(omega, initial_species_conc);
    }
    
    /* ============================= MAIN ENTRY POINT ============================= */
    
    // Calculate equilibrium species concentrations
    std::vector<T> calculate_species_concentrations(const std::vector<T>& initial_conc) {
        size_t nc = component_names.size();
        size_t ns = species_names.size();
        
        if (nc == 0 || ns == 0) return initial_conc;
        
        // Calculate total component concentrations (conserved quantities)
        std::vector<T> T_total = calc_component_totals(initial_conc);
        
        // DEBUG: Print totals being conserved (disabled for production)
        // Uncomment below to enable debug output for first 3 calls
        /*
        static plint eq_debug_calls = 0;
        if (eq_debug_calls < 3) {
            std::cout << "[EQ_SOLVER] Input conc: ";
            for (size_t i = 0; i < initial_conc.size(); ++i) {
                std::cout << initial_conc[i] << " ";
            }
            std::cout << std::endl;
            std::cout << "[EQ_SOLVER] Component totals: ";
            for (size_t j = 0; j < T_total.size(); ++j) {
                std::cout << component_names[j] << "=" << T_total[j] << " ";
            }
            std::cout << std::endl;
            eq_debug_calls++;
        }
        */
        
        // Solve equilibrium
        std::vector<T> result = solve_equilibrium_anderson(initial_conc, T_total);
        
        // DEBUG: Print result (disabled for production)
        /*
        if (eq_debug_calls <= 3) {
            std::cout << "[EQ_SOLVER] Result: ";
            for (size_t i = 0; i < result.size(); ++i) {
                std::cout << result[i] << " ";
            }
            std::cout << " (converged=" << lastConverged << ", iter=" << lastIterations << ")" << std::endl;
        }
        */
        
        // Validate and bound results
        for (size_t i = 0; i < result.size(); ++i) {
            if (std::isnan(result[i]) || std::isinf(result[i])) {
                result[i] = (i < initial_conc.size() && initial_conc[i] > MIN_CONC) 
                            ? std::min(initial_conc[i], MAX_CONC) : MIN_CONC;
            }
            result[i] = std::max(std::min(result[i], MAX_CONC), MIN_CONC);
        }
        return result;
    }
    
    /* ============================= STATISTICS ============================= */
    
    void printStatistics() const {
        pcout << "╔══════════════════════════════════════════════════════════════════╗\n";
        pcout << "║  ANDERSON ACCELERATION + PCF SOLVER STATISTICS                   ║\n";
        pcout << "╠══════════════════════════════════════════════════════════════════╣\n";
        pcout << "║  Total solves:    " << std::setw(10) << totalSolves 
              << "                                ║\n";
        pcout << "║  Converged:       " << std::setw(10) << totalConverged << " (" 
              << std::fixed << std::setprecision(1) 
              << (totalSolves > 0 ? 100.0 * totalConverged / totalSolves : 0.0) 
              << "%)                       ║\n";
        pcout << "║  Did not converge:" << std::setw(10) << totalDiverged 
              << "                                ║\n";
        pcout << "╚══════════════════════════════════════════════════════════════════╝\n";
    }
    
private:
    std::vector<std::string> species_names, component_names;
    std::vector<T> logK_values;
    std::vector<std::vector<T>> stoich_matrix;
    
    plint maxIterations;
    T tolerance;
    
    mutable bool lastConverged;
    mutable plint lastIterations;
    mutable T lastResidual;
    
    bool verbose;
    
    mutable plint totalSolves, totalConverged, totalDiverged;
    
    plint andersonDepth;
    T conditionTol, beta;
};


/* ===============================================================================================================
   ======================================= EQUILIBRIUM DATA PROCESSORS ===========================================
   =============================================================================================================== */

/* ============================================================================
 * run_equilibrium_biotic - Equilibrium chemistry for biotic simulations
 * ============================================================================
 * 
 * Solves fast equilibrium reactions using Anderson Acceleration + PCF method.
 * Operates on substrate lattices only, preserving biomass concentrations.
 * 
 * LATTICE LAYOUT:
 *   lattices[0 ... subsNum-1] = substrate concentration lattices
 *   lattices[subsNum]         = mask lattice
 * 
 * USAGE (Operator Splitting - call AFTER kinetics):
 *   1. Transport (LBM advection-diffusion)
 *   2. Kinetics (run_kinetics)
 *   3. Update reaction lattices (update_rxnLattices)
 *   4. Equilibrium (run_equilibrium_biotic) <-- THIS PROCESSOR
 * 
 * ============================================================================ */

template<typename T, template<typename U> class Descriptor>
class run_equilibrium_biotic : public LatticeBoxProcessingFunctional3D<T, Descriptor>
{
public:
    run_equilibrium_biotic(plint nx_, plint subsNum_, EquilibriumChemistry<T>& eqChem_, 
                           plint solid_, plint bb_)
        : nx(nx_), subsNum(subsNum_), eqChem(eqChem_), solid(solid_), bb(bb_), 
          maskLloc(subsNum_)
    {}

    virtual void process(Box3D domain, std::vector<BlockLattice3D<T, Descriptor>*> lattices) {
        Dot3D absoluteOffset = lattices[0]->getLocation();
        
        // ═══════════════════════════════════════════════════════════════════════
        // DEBUG CONTROL - All disabled for production
        // ═══════════════════════════════════════════════════════════════════════

        for (plint iX = domain.x0; iX <= domain.x1; ++iX) {
            plint absX = iX + absoluteOffset.x;

            if (absX > 0 && absX < nx - 1) {
                for (plint iY = domain.y0; iY <= domain.y1; ++iY) {
                    for (plint iZ = domain.z0; iZ <= domain.z1; ++iZ) {
                        Dot3D maskOffset = computeRelativeDisplacement(*lattices[0], *lattices[maskLloc]);
                        plint mask = util::roundToInt(lattices[maskLloc]->get(
                            iX + maskOffset.x, iY + maskOffset.y, iZ + maskOffset.z).computeDensity());
                        
                        if (mask != solid && mask != bb) {
                            // Compute offsets for all lattices
                            std::vector<Dot3D> vec_offset;
                            for (plint iT = 0; iT <= maskLloc; ++iT) {
                                vec_offset.push_back(computeRelativeDisplacement(*lattices[0], *lattices[iT]));
                            }

                            // Extract current substrate concentrations
                            std::vector<T> conc(subsNum);
                            for (plint iS = 0; iS < subsNum; ++iS) {
                                plint iXs = iX + vec_offset[iS].x;
                                plint iYs = iY + vec_offset[iS].y;
                                plint iZs = iZ + vec_offset[iS].z;
                                T c0 = lattices[iS]->get(iXs, iYs, iZs).computeDensity();
                                conc[iS] = std::max(c0, EquilibriumChemistry<T>::MIN_CONC);
                            }

                            // Solve equilibrium chemistry
                            std::vector<T> eq_conc = eqChem.calculate_species_concentrations(conc);

                            // Update substrate lattices with equilibrium changes
                            for (plint iS = 0; iS < subsNum; ++iS) {
                                T dC = eq_conc[iS] - conc[iS];
                                
                                // ═══════════════════════════════════════════════════════════
                                // SAFEGUARD: Limit maximum change per timestep
                                // ═══════════════════════════════════════════════════════════
                                const T MAX_RELATIVE_CHANGE = 0.1;  // Max 10% change per step
                                const T MAX_ABSOLUTE_CHANGE = 1e-4; // Max absolute change
                                
                                T max_allowed = std::max(MAX_ABSOLUTE_CHANGE, 
                                                         MAX_RELATIVE_CHANGE * std::abs(conc[iS]));
                                if (std::abs(dC) > max_allowed) {
                                    dC = (dC > 0) ? max_allowed : -max_allowed;
                                }
                                
                                // Ensure new concentration stays positive
                                T new_conc = conc[iS] + dC;
                                if (new_conc < 1e-20) {
                                    dC = 1e-20 - conc[iS];  // Adjust dC to reach minimum
                                }
                                // ═══════════════════════════════════════════════════════════

                                if (std::abs(dC) > thrd) {
                                    Array<T, 7> g;
                                    plint iXt = iX + vec_offset[iS].x;
                                    plint iYt = iY + vec_offset[iS].y;
                                    plint iZt = iZ + vec_offset[iS].z;
                                    lattices[iS]->get(iXt, iYt, iZt).getPopulations(g);

                                    // D3Q7 weights: w0=1/4, w1-w6=1/8
                                    g[0] += dC / 4.0;
                                    g[1] += dC / 8.0;
                                    g[2] += dC / 8.0;
                                    g[3] += dC / 8.0;
                                    g[4] += dC / 8.0;
                                    g[5] += dC / 8.0;
                                    g[6] += dC / 8.0;

                                    lattices[iS]->get(iXt, iYt, iZt).setPopulations(g);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulkAndEnvelope;
    }

    virtual run_equilibrium_biotic<T, Descriptor>* clone() const {
        return new run_equilibrium_biotic<T, Descriptor>(*this);
    }

    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        for (plint iS = 0; iS < subsNum; ++iS) {
            modified[iS] = modif::staticVariables;
        }
        modified[maskLloc] = modif::nothing;
    }

private:
    plint nx;
    plint subsNum;
    EquilibriumChemistry<T>& eqChem;
    plint solid, bb;
    plint maskLloc;
};


/* ============================================================================
 * run_equilibrium_full - Equilibrium with delta lattices
 * ============================================================================
 * 
 * Alternative version that stores changes in delta lattices.
 * Use this if you need to accumulate equilibrium changes before applying them.
 * 
 * LATTICE LAYOUT:
 *   lattices[0 ... subsNum-1]           = substrate concentration lattices
 *   lattices[subsNum ... 2*subsNum-1]   = delta concentration lattices (dC)
 *   lattices[2*subsNum]                 = mask lattice
 * 
 * ============================================================================ */

template<typename T, template<typename U> class Descriptor>
class run_equilibrium_full : public LatticeBoxProcessingFunctional3D<T, Descriptor>
{
public:
    run_equilibrium_full(plint nx_, plint subsNum_, EquilibriumChemistry<T>& eqChem_, 
                         plint solid_, plint bb_)
        : nx(nx_), subsNum(subsNum_), eqChem(eqChem_), solid(solid_), bb(bb_), 
          dCloc(subsNum_), maskLloc(2 * subsNum_)
    {}

    virtual void process(Box3D domain, std::vector<BlockLattice3D<T, Descriptor>*> lattices) {
        Dot3D absoluteOffset = lattices[0]->getLocation();

        for (plint iX = domain.x0; iX <= domain.x1; ++iX) {
            plint absX = iX + absoluteOffset.x;

            if (absX > 0 && absX < nx - 1) {
                for (plint iY = domain.y0; iY <= domain.y1; ++iY) {
                    for (plint iZ = domain.z0; iZ <= domain.z1; ++iZ) {
                        Dot3D maskOffset = computeRelativeDisplacement(*lattices[0], *lattices[maskLloc]);
                        plint mask = util::roundToInt(lattices[maskLloc]->get(
                            iX + maskOffset.x, iY + maskOffset.y, iZ + maskOffset.z).computeDensity());
                        
                        if (mask != solid && mask != bb) {
                            std::vector<Dot3D> vec_offset;
                            for (plint iT = 0; iT <= maskLloc; ++iT) {
                                vec_offset.push_back(computeRelativeDisplacement(*lattices[0], *lattices[iT]));
                            }

                            // Extract current concentrations
                            std::vector<T> conc(subsNum);
                            for (plint iS = 0; iS < subsNum; ++iS) {
                                plint iXs = iX + vec_offset[iS].x;
                                plint iYs = iY + vec_offset[iS].y;
                                plint iZs = iZ + vec_offset[iS].z;
                                T c0 = lattices[iS]->get(iXs, iYs, iZs).computeDensity();
                                conc[iS] = std::max(c0, EquilibriumChemistry<T>::MIN_CONC);
                            }

                            // Solve equilibrium
                            std::vector<T> eq_conc = eqChem.calculate_species_concentrations(conc);

                            // Store changes in delta lattices
                            for (plint iS = 0; iS < subsNum; ++iS) {
                                T dC = eq_conc[iS] - conc[iS];

                                if (std::abs(dC) > thrd) {
                                    Array<T, 7> g;
                                    plint iXd = iX + vec_offset[iS + dCloc].x;
                                    plint iYd = iY + vec_offset[iS + dCloc].y;
                                    plint iZd = iZ + vec_offset[iS + dCloc].z;
                                    lattices[iS + dCloc]->get(iXd, iYd, iZd).getPopulations(g);

                                    g[0] += dC / 4.0;
                                    g[1] += dC / 8.0;
                                    g[2] += dC / 8.0;
                                    g[3] += dC / 8.0;
                                    g[4] += dC / 8.0;
                                    g[5] += dC / 8.0;
                                    g[6] += dC / 8.0;

                                    lattices[iS + dCloc]->get(iXd, iYd, iZd).setPopulations(g);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulkAndEnvelope;
    }

    virtual run_equilibrium_full<T, Descriptor>* clone() const {
        return new run_equilibrium_full<T, Descriptor>(*this);
    }

    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        for (plint iS = 0; iS < subsNum; ++iS) {
            modified[iS] = modif::nothing;
        }
        for (plint iS = 0; iS < subsNum; ++iS) {
            modified[iS + dCloc] = modif::staticVariables;
        }
        modified[maskLloc] = modif::nothing;
    }

private:
    plint nx;
    plint subsNum;
    EquilibriumChemistry<T>& eqChem;
    plint solid, bb;
    plint dCloc, maskLloc;
};


/* ============================================================================
 * update_equilibriumLattices - Apply delta changes from equilibrium
 * ============================================================================
 * 
 * Companion processor to run_equilibrium_full.
 * 
 * LATTICE LAYOUT:
 *   lattices[0 ... subsNum-1]           = substrate concentration lattices
 *   lattices[subsNum ... 2*subsNum-1]   = delta concentration lattices (dC)
 *   lattices[2*subsNum]                 = mask lattice
 * 
 * ============================================================================ */

template<typename T, template<typename U> class Descriptor>
class update_equilibriumLattices : public LatticeBoxProcessingFunctional3D<T, Descriptor>
{
public:
    update_equilibriumLattices(plint nx_, plint subsNum_, plint solid_, plint bb_)
        : nx(nx_), subsNum(subsNum_), solid(solid_), bb(bb_), 
          dCloc(subsNum_), maskLloc(2 * subsNum_)
    {}

    virtual void process(Box3D domain, std::vector<BlockLattice3D<T, Descriptor>*> lattices) {
        Dot3D absoluteOffset = lattices[0]->getLocation();
        
        for (plint iX = domain.x0; iX <= domain.x1; ++iX) {
            plint absX = iX + absoluteOffset.x;
            
            if (absX > 0 && absX < nx - 1) {
                for (plint iY = domain.y0; iY <= domain.y1; ++iY) {
                    for (plint iZ = domain.z0; iZ <= domain.z1; ++iZ) {
                        Dot3D maskOffset = computeRelativeDisplacement(*lattices[0], *lattices[maskLloc]);
                        plint mask = util::roundToInt(lattices[maskLloc]->get(
                            iX + maskOffset.x, iY + maskOffset.y, iZ + maskOffset.z).computeDensity());
                        
                        if (mask != solid && mask != bb) {
                            std::vector<Dot3D> vec_offset;
                            for (plint iT = 0; iT <= maskLloc; ++iT) {
                                vec_offset.push_back(computeRelativeDisplacement(*lattices[0], *lattices[iT]));
                            }

                            for (plint iS = 0; iS < subsNum; ++iS) {
                                plint iXd = iX + vec_offset[iS + dCloc].x;
                                plint iYd = iY + vec_offset[iS + dCloc].y;
                                plint iZd = iZ + vec_offset[iS + dCloc].z;
                                T dC = lattices[iS + dCloc]->get(iXd, iYd, iZd).computeDensity();
                                
                                if (std::abs(dC) > thrd) {
                                    Array<T, 7> g;
                                    plint iXs = iX + vec_offset[iS].x;
                                    plint iYs = iY + vec_offset[iS].y;
                                    plint iZs = iZ + vec_offset[iS].z;
                                    lattices[iS]->get(iXs, iYs, iZs).getPopulations(g);

                                    g[0] += dC / 4.0;
                                    g[1] += dC / 8.0;
                                    g[2] += dC / 8.0;
                                    g[3] += dC / 8.0;
                                    g[4] += dC / 8.0;
                                    g[5] += dC / 8.0;
                                    g[6] += dC / 8.0;

                                    lattices[iS]->get(iXs, iYs, iZs).setPopulations(g);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulkAndEnvelope;
    }

    virtual update_equilibriumLattices<T, Descriptor>* clone() const {
        return new update_equilibriumLattices<T, Descriptor>(*this);
    }

    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        for (plint iS = 0; iS < subsNum; ++iS) {
            modified[iS] = modif::staticVariables;
        }
        for (plint iS = 0; iS < subsNum; ++iS) {
            modified[iS + dCloc] = modif::nothing;
        }
        modified[maskLloc] = modif::nothing;
    }

private:
    plint nx;
    plint subsNum;
    plint solid, bb;
    plint dCloc, maskLloc;
};


/* ============================================================================
 * reset_deltaLattices - Reset delta lattices to zero
 * ============================================================================
 * 
 * LATTICE LAYOUT:
 *   lattices[0 ... numDelta-1] = delta lattices to reset
 *   lattices[numDelta]         = mask lattice
 * 
 * ============================================================================ */

template<typename T, template<typename U> class Descriptor>
class reset_deltaLattices : public LatticeBoxProcessingFunctional3D<T, Descriptor>
{
public:
    reset_deltaLattices(plint nx_, plint numDelta_, plint solid_, plint bb_)
        : nx(nx_), numDelta(numDelta_), solid(solid_), bb(bb_), maskLloc(numDelta_)
    {}

    virtual void process(Box3D domain, std::vector<BlockLattice3D<T, Descriptor>*> lattices) {
        Dot3D absoluteOffset = lattices[0]->getLocation();
        
        // Zero density populations: g[0]=(0-1)/4=-0.25, g[1-6]=(0-1)/8=-0.125
        Array<T, 7> g_zero;
        g_zero[0] = -0.25;
        g_zero[1] = g_zero[2] = g_zero[3] = g_zero[4] = g_zero[5] = g_zero[6] = -0.125;
        
        for (plint iX = domain.x0; iX <= domain.x1; ++iX) {
            plint absX = iX + absoluteOffset.x;
            
            if (absX > 0 && absX < nx - 1) {
                for (plint iY = domain.y0; iY <= domain.y1; ++iY) {
                    for (plint iZ = domain.z0; iZ <= domain.z1; ++iZ) {
                        Dot3D maskOffset = computeRelativeDisplacement(*lattices[0], *lattices[maskLloc]);
                        plint mask = util::roundToInt(lattices[maskLloc]->get(
                            iX + maskOffset.x, iY + maskOffset.y, iZ + maskOffset.z).computeDensity());
                        
                        if (mask != solid && mask != bb) {
                            for (plint iD = 0; iD < numDelta; ++iD) {
                                Dot3D offset = computeRelativeDisplacement(*lattices[0], *lattices[iD]);
                                plint iXd = iX + offset.x;
                                plint iYd = iY + offset.y;
                                plint iZd = iZ + offset.z;
                                lattices[iD]->get(iXd, iYd, iZd).setPopulations(g_zero);
                            }
                        }
                    }
                }
            }
        }
    }

    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulkAndEnvelope;
    }

    virtual reset_deltaLattices<T, Descriptor>* clone() const {
        return new reset_deltaLattices<T, Descriptor>(*this);
    }

    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        for (plint iD = 0; iD < numDelta; ++iD) {
            modified[iD] = modif::staticVariables;
        }
        modified[maskLloc] = modif::nothing;
    }

private:
    plint nx;
    plint numDelta;
    plint solid, bb;
    plint maskLloc;
};


/* ===============================================================================================================
   ============================================= PART 4 SUMMARY ==================================================
   ===============================================================================================================
   
   EQUILIBRIUM CHEMISTRY CLASS:
   ----------------------------
   EquilibriumChemistry<T>          - Anderson Acceleration + PCF solver
     - setSpeciesNames()            - Set species participating in equilibrium
     - setComponentNames()          - Set master components
     - setLogK()                    - Set equilibrium constants
     - setStoichiometryMatrix()     - Set stoichiometry matrix
     - calculate_species_concentrations() - Main solver entry point
     - printStatistics()            - Print convergence statistics
   
   EQUILIBRIUM DATA PROCESSORS:
   ----------------------------
   run_equilibrium_biotic           - Direct equilibrium update (RECOMMENDED)
     Lattices: [substrates..., mask]
     
   run_equilibrium_full             - Equilibrium with delta lattices
     Lattices: [substrates..., delta_substrates..., mask]
     
   update_equilibriumLattices       - Apply delta changes from equilibrium
     Lattices: [substrates..., delta_substrates..., mask]
     
   reset_deltaLattices              - Reset delta lattices to zero
     Lattices: [deltas..., mask]
   
   =============================================================================================================== */

#endif // COMPLAB3D_PROCESSORS_PART4_HH
