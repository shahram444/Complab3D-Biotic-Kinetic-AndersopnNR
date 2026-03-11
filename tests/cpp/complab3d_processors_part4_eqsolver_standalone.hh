// Standalone extract of EquilibriumChemistry class from
// src/complab3d_processors_part4_eqsolver.hh for unit testing.
// Only the EquilibriumChemistry<T> class is included here -- the Palabos
// lattice-processor wrappers (run_equilibrium_biotic, etc.) are excluded
// because they depend on the full Palabos library.
//
// IMPORTANT: This file is auto-extracted from the production header.
// If the solver logic changes, regenerate this file.

#ifndef COMPLAB3D_EQSOLVER_STANDALONE_HH
#define COMPLAB3D_EQSOLVER_STANDALONE_HH

#include <cmath>
#include <limits>
#include <vector>
#include <string>
#include <algorithm>
#include <iomanip>
#include <iostream>

using plb::plint;

template<typename T>
class EquilibriumChemistry
{
public:
    static constexpr T MIN_CONC = 1e-30;
    static constexpr T MAX_CONC = 10.0;
    static constexpr T MIN_LOG_C = -30.0;
    static constexpr T MAX_LOG_C = 1.0;
    static constexpr plint DEFAULT_ANDERSON_DEPTH = 4;
    static constexpr T DEFAULT_CONDITION_TOL = 1e10;
    static constexpr T DEFAULT_BETA = 1.0;

    EquilibriumChemistry()
        : maxIterations(200), tolerance(1e-8), lastConverged(true),
          lastIterations(0), lastResidual(0.0), verbose(false),
          totalSolves(0), totalConverged(0), totalDiverged(0),
          andersonDepth(DEFAULT_ANDERSON_DEPTH),
          conditionTol(DEFAULT_CONDITION_TOL), beta(DEFAULT_BETA) {}

    void setSpeciesNames(const std::vector<std::string>& names) {
        species_names.clear();
        for (const auto& name : names) {
            if (name != "H2O" && name != "h2o") species_names.push_back(name);
        }
    }
    void setComponentNames(const std::vector<std::string>& names) { component_names = names; }
    void setLogK(const std::vector<T>& logK) { logK_values = logK; }
    void setStoichiometryMatrix(const std::vector<std::vector<T>>& S) { stoich_matrix = S; }
    void setMaxIterations(plint maxIter) { maxIterations = maxIter; }
    void setTolerance(T tol) { tolerance = tol; }
    void setVerbose(bool v) { verbose = v; }
    void setAndersonDepth(plint depth) { andersonDepth = std::max(plint(1), depth); }
    void setConditionTolerance(T condTol) { conditionTol = condTol; }
    void setBeta(T betaVal) { beta = betaVal; }

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

    void resetStatistics() { totalSolves = totalConverged = totalDiverged = 0; }

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

    std::vector<T> calc_species(const std::vector<T>& logC,
                                const std::vector<T>& initial_conc = std::vector<T>()) const {
        size_t ns = species_names.size();
        size_t nc = component_names.size();
        std::vector<T> conc(ns);
        for (size_t i = 0; i < ns; ++i) {
            if (!isEquilibriumSpecies(i)) {
                conc[i] = (i < initial_conc.size() && initial_conc[i] > MIN_CONC)
                          ? std::min(initial_conc[i], MAX_CONC) : MIN_CONC;
                continue;
            }
            T logConc = (i < logK_values.size()) ? logK_values[i] : 0.0;
            for (size_t j = 0; j < nc; ++j) {
                if (j < stoich_matrix[i].size()) {
                    logConc += stoich_matrix[i][j] * logC[j];
                }
            }
            logConc = std::max(std::min(logConc, MAX_LOG_C), MIN_LOG_C);
            conc[i] = std::pow(10.0, logConc);
            if (std::isnan(conc[i]) || std::isinf(conc[i])) {
                conc[i] = (i < initial_conc.size() && initial_conc[i] > MIN_CONC)
                          ? initial_conc[i] : MIN_CONC;
            }
            conc[i] = std::max(std::min(conc[i], MAX_CONC), MIN_CONC);
        }
        return conc;
    }

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
                if (mu_ij > 1e-15) sum_positive += mu_ij * c_i;
                else if (mu_ij < -1e-15) sum_negative += std::abs(mu_ij) * c_i;
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

    std::vector<T> pcf_residual(const std::vector<T>& logC, const std::vector<T>& T_total,
                                const std::vector<T>& initial_conc) const {
        size_t nc = component_names.size();
        std::vector<T> species_conc = calc_species(logC, initial_conc);
        auto sums = calc_reactive_product_sums(species_conc, T_total);
        const std::vector<T>& S_R = sums.first;
        const std::vector<T>& S_P = sums.second;
        std::vector<T> f(nc);
        for (size_t j = 0; j < nc; ++j) {
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

    T norm(const std::vector<T>& v) const {
        T s = 0; for (T x : v) s += x * x; return std::sqrt(s);
    }
    std::vector<T> vec_subtract(const std::vector<T>& a, const std::vector<T>& b) const {
        std::vector<T> r(a.size());
        for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] - (i < b.size() ? b[i] : 0.0);
        return r;
    }
    std::vector<T> vec_add(const std::vector<T>& a, const std::vector<T>& b) const {
        std::vector<T> r(a.size());
        for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] + (i < b.size() ? b[i] : 0.0);
        return r;
    }
    T dot_product(const std::vector<T>& a, const std::vector<T>& b) const {
        T sum = 0; for (size_t i = 0; i < a.size() && i < b.size(); ++i) sum += a[i] * b[i];
        return sum;
    }

    void qr_decomposition(const std::vector<std::vector<T>>& columns,
                          std::vector<std::vector<T>>& Q,
                          std::vector<std::vector<T>>& R, T& condNum) const {
        size_t m = columns.size();
        if (m == 0) { condNum = 1.0; return; }
        size_t n = columns[0].size();
        Q.resize(m); R.resize(m, std::vector<T>(m, 0.0));
        T R_max = 0.0, R_min = std::numeric_limits<T>::max();
        for (size_t j = 0; j < m; ++j) {
            Q[j] = columns[j];
            for (size_t i = 0; i < j; ++i) {
                R[i][j] = dot_product(Q[i], columns[j]);
                for (size_t k = 0; k < n; ++k) Q[j][k] -= R[i][j] * Q[i][k];
            }
            R[j][j] = norm(Q[j]);
            if (R[j][j] > 1e-15) { for (size_t k = 0; k < n; ++k) Q[j][k] /= R[j][j]; }
            T absR = std::abs(R[j][j]);
            if (absR > R_max) R_max = absR;
            if (absR > 1e-30 && absR < R_min) R_min = absR;
        }
        condNum = (R_min > 1e-30) ? R_max / R_min : std::numeric_limits<T>::max();
    }

    std::vector<T> solve_upper_triangular(const std::vector<std::vector<T>>& R,
                                          const std::vector<T>& b) const {
        size_t m = R.size();
        std::vector<T> x(m, 0.0);
        for (int i = m - 1; i >= 0; --i) {
            x[i] = b[i];
            for (size_t j = i + 1; j < m; ++j) x[i] -= R[i][j] * x[j];
            if (std::abs(R[i][i]) > 1e-30) x[i] /= R[i][i];
        }
        return x;
    }

    std::vector<T> solve_equilibrium_anderson(const std::vector<T>& initial_species_conc,
                                              const std::vector<T>& T_total) {
        lastConverged = false; lastIterations = 0; lastResidual = 0.0; totalSolves++;
        size_t nc = component_names.size();
        if (nc == 0) { lastConverged = true; totalConverged++; return initial_species_conc; }

        std::vector<T> omega(nc);
        for (size_t j = 0; j < nc; ++j) {
            auto it = std::find(species_names.begin(), species_names.end(), component_names[j]);
            T comp_conc = 1e-7;
            if (it != species_names.end()) {
                size_t idx = std::distance(species_names.begin(), it);
                if (idx < initial_species_conc.size()) comp_conc = initial_species_conc[idx];
            }
            comp_conc = std::max(std::min(comp_conc, MAX_CONC), MIN_CONC);
            omega[j] = std::log10(comp_conc);
        }

        std::vector<T> f0 = pcf_residual(omega, T_total, initial_species_conc);
        std::vector<T> omega_new = vec_add(omega, f0);
        for (size_t j = 0; j < nc; ++j)
            omega_new[j] = std::max(std::min(omega_new[j], MAX_LOG_C), MIN_LOG_C);

        std::vector<std::vector<T>> omega_history, f_history;
        omega_history.push_back(omega); f_history.push_back(f0);
        omega = omega_new;

        for (plint iter = 1; iter < maxIterations; ++iter) {
            lastIterations = iter;
            std::vector<T> f_k = pcf_residual(omega, T_total, initial_species_conc);
            T f_norm = norm(f_k); lastResidual = f_norm;
            if (f_norm < tolerance) {
                lastConverged = true; totalConverged++;
                return calc_species(omega, initial_species_conc);
            }

            omega_history.push_back(omega); f_history.push_back(f_k);
            plint m_k = std::min(andersonDepth, (plint)(f_history.size() - 1));

            if (m_k < 1) {
                omega_new = vec_add(omega, f_k);
            } else {
                std::vector<std::vector<T>> Delta_F, Delta_X;
                size_t hist_size = f_history.size();
                for (plint i = 0; i < m_k; ++i) {
                    size_t idx = hist_size - m_k - 1 + i;
                    Delta_F.push_back(vec_subtract(f_history[idx + 1], f_history[idx]));
                    Delta_X.push_back(vec_subtract(omega_history[idx + 1], omega_history[idx]));
                }
                std::vector<std::vector<T>> Q, R; T condNum;
                qr_decomposition(Delta_F, Q, R, condNum);
                while (condNum > conditionTol && Delta_F.size() > 1) {
                    Delta_F.erase(Delta_F.begin()); Delta_X.erase(Delta_X.begin());
                    qr_decomposition(Delta_F, Q, R, condNum);
                }
                std::vector<T> Qt_fk(Delta_F.size());
                for (size_t i = 0; i < Delta_F.size(); ++i) Qt_fk[i] = dot_product(Q[i], f_k);
                std::vector<T> gamma = solve_upper_triangular(R, Qt_fk);
                std::vector<T> DX_gamma(nc, 0.0), DF_gamma(nc, 0.0);
                for (size_t i = 0; i < Delta_X.size() && i < gamma.size(); ++i) {
                    for (size_t j = 0; j < nc; ++j) {
                        DX_gamma[j] += Delta_X[i][j] * gamma[i];
                        DF_gamma[j] += Delta_F[i][j] * gamma[i];
                    }
                }
                omega_new.resize(nc);
                for (size_t j = 0; j < nc; ++j)
                    omega_new[j] = omega[j] - DX_gamma[j] + beta * (f_k[j] - DF_gamma[j]);
            }

            for (size_t j = 0; j < nc; ++j) {
                omega_new[j] = std::max(std::min(omega_new[j], MAX_LOG_C), MIN_LOG_C);
                if (std::isnan(omega_new[j]) || std::isinf(omega_new[j])) omega_new[j] = omega[j];
            }
            omega = omega_new;
            while (omega_history.size() > (size_t)(andersonDepth + 1)) {
                omega_history.erase(omega_history.begin()); f_history.erase(f_history.begin());
            }
        }
        totalDiverged++;
        return calc_species(omega, initial_species_conc);
    }

    std::vector<T> calculate_species_concentrations(const std::vector<T>& initial_conc) {
        size_t nc = component_names.size();
        size_t ns = species_names.size();
        if (nc == 0 || ns == 0) return initial_conc;
        std::vector<T> T_total = calc_component_totals(initial_conc);
        std::vector<T> result = solve_equilibrium_anderson(initial_conc, T_total);
        for (size_t i = 0; i < result.size(); ++i) {
            if (std::isnan(result[i]) || std::isinf(result[i])) {
                result[i] = (i < initial_conc.size() && initial_conc[i] > MIN_CONC)
                            ? std::min(initial_conc[i], MAX_CONC) : MIN_CONC;
            }
            result[i] = std::max(std::min(result[i], MAX_CONC), MIN_CONC);
        }
        return result;
    }

    void printStatistics() const {
        std::cout << "Total solves: " << totalSolves
                  << " Converged: " << totalConverged
                  << " Diverged: " << totalDiverged << "\n";
    }

private:
    std::vector<std::string> species_names, component_names;
    std::vector<T> logK_values;
    std::vector<std::vector<T>> stoich_matrix;
    plint maxIterations; T tolerance;
    mutable bool lastConverged; mutable plint lastIterations; mutable T lastResidual;
    bool verbose;
    mutable plint totalSolves, totalConverged, totalDiverged;
    plint andersonDepth; T conditionTol, beta;
};

// C++11 requires out-of-class definitions for static constexpr members
// that are ODR-used (e.g., passed by reference, used with EXPECT_GE/LE).
template<typename T> constexpr T EquilibriumChemistry<T>::MIN_CONC;
template<typename T> constexpr T EquilibriumChemistry<T>::MAX_CONC;
template<typename T> constexpr T EquilibriumChemistry<T>::MIN_LOG_C;
template<typename T> constexpr T EquilibriumChemistry<T>::MAX_LOG_C;
template<typename T> constexpr plint EquilibriumChemistry<T>::DEFAULT_ANDERSON_DEPTH;
template<typename T> constexpr T EquilibriumChemistry<T>::DEFAULT_CONDITION_TOL;
template<typename T> constexpr T EquilibriumChemistry<T>::DEFAULT_BETA;

#endif // COMPLAB3D_EQSOLVER_STANDALONE_HH
