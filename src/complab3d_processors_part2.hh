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

#ifndef COMPLAB3D_PROCESSORS_PART2_HH
#define COMPLAB3D_PROCESSORS_PART2_HH

#include <random>
using namespace plb;
typedef double T;

/* ===============================================================================================================
   ======================================= MASK AND DYNAMICS UPDATE PROCESSORS ===================================
   =============================================================================================================== */

// Update nonlocal mask number at every timestep
template<typename T, template<typename U> class Descriptor>
class updateLocalMaskNtotalLattices3D : public LatticeBoxProcessingFunctional3D<T,Descriptor>
{
public:
    updateLocalMaskNtotalLattices3D(plint nx_, plint ny_, plint nz_, plint length_, plint bb_, plint solid_, std::vector<std::vector<plint>> bio_, std::vector<plint> pore_, T bMassFrac_, T maxbMassRho_)
    : nx(nx_), ny(ny_), nz(nz_), length(length_), bb(bb_), solid(solid_), bio(bio_), pore(pore_), thrdbMassRho(bMassFrac_*maxbMassRho_)
    {}
    // lattices[0~(#ofbM-1)] = original biomass lattices
    // lattices[#ofbM~(len-3)] = copy biomass lattices
    // lattices[len-3] = total biomass lattice
    // lattices[len-2] = mask lattice
    // lattices[len-1] = age lattice
    virtual void process(Box3D domain, std::vector<BlockLattice3D<T,Descriptor>*> lattices) {
        plint maskLloc = length-2, bMtLloc = length-3;
        std::vector<Dot3D> vec_offset;
        Dot3D absoluteOffset = lattices[0]->getLocation();
        for (plint iL=0; iL<length; ++iL) { vec_offset.push_back(computeRelativeDisplacement(*lattices[0],*lattices[iL])); }
        for (plint iX=domain.x0; iX<=domain.x1; ++iX) {
            plint iXm = iX+vec_offset[maskLloc].x;
            for (plint iY=domain.y0; iY<=domain.y1; ++iY) {
                plint iYm = iY+vec_offset[maskLloc].y;
                for (plint iZ=domain.z0; iZ<=domain.z1; ++iZ) {
                    plint iZm = iZ+vec_offset[maskLloc].z;
                    plint mask = util::roundToInt( lattices[maskLloc]->get(iXm,iYm,iZm).computeDensity() );
                    if (mask != bb && mask != solid) {
                        T bmass = 0.; plint newmask = 0;
                        T bMt = lattices[bMtLloc]->get(iX+vec_offset[bMtLloc].x,iY+vec_offset[bMtLloc].y,iZ+vec_offset[bMtLloc].z).computeDensity();
                        for (size_t iM=0; iM<bio.size(); ++iM) {
                            T bm = lattices[iM]->get(iX+vec_offset[iM].x,iY+vec_offset[iM].y,iZ+vec_offset[iM].z).computeDensity();
                            if ( bm > COMPLAB_THRD) { bmass += bm; newmask += bio[iM][0];}
                        }
                        // update total biomass density
                        if ( std::abs(bmass-bMt) > COMPLAB_THRD) {
                            Array<T,7> g;
                            g[0]=(T) (bmass-1)/4; g[1]=g[2]=g[3]=g[4]=g[5]=g[6]=(T) (bmass-1)/8;
                            plint iXt = iX+vec_offset[bMtLloc].x, iYt = iY+vec_offset[bMtLloc].y, iZt = iZ+vec_offset[bMtLloc].z;
                            lattices[bMtLloc]->get(iXt,iYt,iZt).setPopulations(g);
                        }
                        // update mask number
                        bool poreflag = 0;
                        for (size_t iP=0; iP<pore.size(); ++iP) {
                            if (mask == pore[iP]) { poreflag = 1; break; }
                        }
                        if (poreflag == 0 && bmass < thrdbMassRho) {
                            newmask = pore[0];
                            if (pore.size()>1) {
                                plint absX = iX + absoluteOffset.x, absY = iY + absoluteOffset.y, absZ = iZ + absoluteOffset.z;
                                plint nbrs = 0;
                                std::vector<plint> delXYZ;
                                
                                // Determine neighbors based on boundary position (3D version)
                                bool atXmin = (absX == 0);
                                bool atXmax = (absX == nx-1);
                                bool atYmin = (absY == 0);
                                bool atYmax = (absY == ny-1);
                                bool atZmin = (absZ == 0);
                                bool atZmax = (absZ == nz-1);
                                
                                // Add valid neighbors
                                if (!atXmax) { delXYZ.push_back(1); delXYZ.push_back(0); delXYZ.push_back(0); ++nbrs; }
                                if (!atXmin) { delXYZ.push_back(-1); delXYZ.push_back(0); delXYZ.push_back(0); ++nbrs; }
                                if (!atYmax) { delXYZ.push_back(0); delXYZ.push_back(1); delXYZ.push_back(0); ++nbrs; }
                                if (!atYmin) { delXYZ.push_back(0); delXYZ.push_back(-1); delXYZ.push_back(0); ++nbrs; }
                                if (!atZmax) { delXYZ.push_back(0); delXYZ.push_back(0); delXYZ.push_back(1); ++nbrs; }
                                if (!atZmin) { delXYZ.push_back(0); delXYZ.push_back(0); delXYZ.push_back(-1); ++nbrs; }

                                for (plint iT=0; iT<nbrs; ++iT) {
                                    plint delx = delXYZ[iT*3], dely = delXYZ[iT*3+1], delz = delXYZ[iT*3+2];
                                    plint nbrmask = util::roundToInt( lattices[maskLloc]->get(iXm+delx,iYm+dely,iZm+delz).computeDensity() );
                                    if (nbrmask != bb && nbrmask != solid) {
                                        bool nbrporeflag = 0;
                                        for (size_t iP=0; iP<pore.size(); ++iP) {
                                            if (nbrmask == pore[iP]) { nbrporeflag = 1; break; }
                                        }
                                        if (nbrporeflag == 1) { newmask = nbrmask; break; }
                                    }
                                }
                            }
                            Array<T,7> g;
                            g[0]=(T) (newmask-1)/4; g[1]=g[2]=g[3]=g[4]=g[5]=g[6]=(T) (newmask-1)/8;
                            lattices[maskLloc]->get(iXm,iYm,iZm).setPopulations(g);
                        }
                        else if (poreflag == 1 && bmass >= thrdbMassRho) {
                            if (newmask > 0) {
                                Array<T,7> g;
                                g[0]=(T) (newmask-1)/4; g[1]=g[2]=g[3]=g[4]=g[5]=g[6]=(T) (newmask-1)/8;
                                lattices[maskLloc]->get(iXm,iYm,iZm).setPopulations(g);
                            }
                            else {
                                std::cout << "Error: Updating mask failed.\n";
                                exit(EXIT_FAILURE);
                            }
                        }
                    }
                }
            }
        }
    }
    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulk;
    }
    virtual updateLocalMaskNtotalLattices3D<T,Descriptor>* clone() const {
        return new updateLocalMaskNtotalLattices3D<T,Descriptor>(*this);
    }
    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        for (plint iL=0; iL<length-3; ++iL) {
            modified[iL] = modif::nothing;
        }
        modified[length-3] = modif::staticVariables;
        modified[length-2] = modif::staticVariables;
        modified[length-1] = modif::nothing;
    }
private:
    plint nx, ny, nz, length, bb, solid;
    std::vector<std::vector<plint>> bio;
    std::vector<plint> pore;
    T thrdbMassRho;
};

template<typename T, template<typename U> class Descriptor>
class fdDiffusion3D : public LatticeBoxProcessingFunctional3D<T,Descriptor>
{
public:
    fdDiffusion3D(plint nx_, plint ny_, plint nz_, plint length_, plint bdryGap_, T nu_)
    : nx(nx_), ny(ny_), nz(nz_), length(length_), bdryGap(bdryGap_), nu(nu_)
    {}
    // lattices[0~(#ofbM-1)] = original biomass lattices
    // lattices[#ofbM~(len-2)] = copy biomass lattices
    // lattices[len-1] = mask lattice
    virtual void process(Box3D domain, std::vector<BlockLattice3D<T,Descriptor>*> lattices) {
        std::vector<Dot3D> vec_offset;
        plint maskLloc = length-1, numbM = (length-1)/2;
        for (plint iL=0; iL<length; ++iL) {
            vec_offset.push_back(computeRelativeDisplacement(*lattices[0],*lattices[iL]));
        }
        Dot3D absoluteOffset = lattices[0]->getLocation();
        for (plint iX=domain.x0; iX<=domain.x1; ++iX) {
            plint absX = iX + absoluteOffset.x;
            if ( absX >= bdryGap && absX <= nx-1-bdryGap ) {
                for (plint iY=domain.y0; iY<=domain.y1; ++iY) {
                    plint absY = iY + absoluteOffset.y;
                    for (plint iZ=domain.z0; iZ<=domain.z1; ++iZ) {
                        plint absZ = iZ + absoluteOffset.z;
                        // collect mask numbers
                        plint iXm = iX + vec_offset[maskLloc].x, iYm = iY + vec_offset[maskLloc].y, iZm = iZ + vec_offset[maskLloc].z;
                        plint mask = util::roundToInt( lattices[maskLloc]->get(iXm,iYm,iZm).computeDensity() );
                        if (mask > 1) {
                            plint mxp=0,mxn=0,myp=0,myn=0,mzp=0,mzn=0;
                            if ( absX == bdryGap ) { mxp=lattices[maskLloc]->get(iXm+1,iYm,iZm).computeDensity(); }
                            else if ( absX == nx-1-bdryGap ) { mxn=lattices[maskLloc]->get(iXm-1,iYm,iZm).computeDensity(); }
                            else { mxp=lattices[maskLloc]->get(iXm+1,iYm,iZm).computeDensity(); mxn=lattices[maskLloc]->get(iXm-1,iYm,iZm).computeDensity(); }
                            if ( absY == 0 ) { myp=lattices[maskLloc]->get(iXm,iYm+1,iZm).computeDensity(); }
                            else if ( absY == ny-1 ) { myn=lattices[maskLloc]->get(iXm,iYm-1,iZm).computeDensity(); }
                            else { myp=lattices[maskLloc]->get(iXm,iYm+1,iZm).computeDensity(); myn=lattices[maskLloc]->get(iXm,iYm-1,iZm).computeDensity(); }
                            if ( absZ == 0 ) { mzp=lattices[maskLloc]->get(iXm,iYm,iZm+1).computeDensity(); }
                            else if ( absZ == nz-1 ) { mzn=lattices[maskLloc]->get(iXm,iYm,iZm-1).computeDensity(); }
                            else { mzp=lattices[maskLloc]->get(iXm,iYm,iZm+1).computeDensity(); mzn=lattices[maskLloc]->get(iXm,iYm,iZm-1).computeDensity(); }
                            
                            // collect biomass densities
                            std::vector<T> bxp(numbM,0), bxn(numbM,0), byp(numbM,0), byn(numbM,0), bzp(numbM,0), bzn(numbM,0), b0(numbM,0);
                            for (plint iM=0; iM<numbM; ++iM) {
                                plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                b0[iM] = lattices[iM+numbM]->get(iXb,iYb,iZb).computeDensity();
                            }
                            // x-direction
                            if ( absX == bdryGap || mxn < 2) {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    bxp[iM] = lattices[iM+numbM]->get(iXb+1,iYb,iZb).computeDensity();
                                    bxn[iM] = b0[iM];
                                }
                            }
                            else if ( absX == nx-1-bdryGap || mxp < 2 ) {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    bxp[iM] = b0[iM];
                                    bxn[iM] = lattices[iM+numbM]->get(iXb-1,iYb,iZb).computeDensity();
                                }
                            }
                            else {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    bxp[iM] = lattices[iM+numbM]->get(iXb+1,iYb,iZb).computeDensity();
                                    bxn[iM] = lattices[iM+numbM]->get(iXb-1,iYb,iZb).computeDensity();
                                }
                            }
                            // y-direction
                            if ( absY == 0 || myn < 2 ) {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    byp[iM] = lattices[iM+numbM]->get(iXb,iYb+1,iZb).computeDensity();
                                    byn[iM] = b0[iM];
                                }
                            }
                            else if ( absY == ny-1 || myp < 2 ) {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    byp[iM] = b0[iM];
                                    byn[iM] = lattices[iM+numbM]->get(iXb,iYb-1,iZb).computeDensity();
                                }
                            }
                            else {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    byp[iM] = lattices[iM+numbM]->get(iXb,iYb+1,iZb).computeDensity();
                                    byn[iM] = lattices[iM+numbM]->get(iXb,iYb-1,iZb).computeDensity();
                                }
                            }
                            // z-direction
                            if ( absZ == 0 || mzn < 2 ) {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    bzp[iM] = lattices[iM+numbM]->get(iXb,iYb,iZb+1).computeDensity();
                                    bzn[iM] = b0[iM];
                                }
                            }
                            else if ( absZ == nz-1 || mzp < 2 ) {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    bzp[iM] = b0[iM];
                                    bzn[iM] = lattices[iM+numbM]->get(iXb,iYb,iZb-1).computeDensity();
                                }
                            }
                            else {
                                for (plint iM=0; iM<numbM; ++iM) {
                                    plint iXb = iX + vec_offset[iM+numbM].x, iYb = iY + vec_offset[iM+numbM].y, iZb = iZ + vec_offset[iM+numbM].z;
                                    bzp[iM] = lattices[iM+numbM]->get(iXb,iYb,iZb+1).computeDensity();
                                    bzn[iM] = lattices[iM+numbM]->get(iXb,iYb,iZb-1).computeDensity();
                                }
                            }
                            
                            for (plint iM=0; iM<numbM; ++iM) {
                                if (b0[iM] < COMPLAB_THRD ) b0[iM]=0;
                                if (bxp[iM] < COMPLAB_THRD ) bxp[iM]=0;
                                if (bxn[iM] < COMPLAB_THRD ) bxn[iM]=0;
                                if (byp[iM] < COMPLAB_THRD ) byp[iM]=0;
                                if (byn[iM] < COMPLAB_THRD ) byn[iM]=0;
                                if (bzp[iM] < COMPLAB_THRD ) bzp[iM]=0;
                                if (bzn[iM] < COMPLAB_THRD ) bzn[iM]=0;
                                // 3D Laplacian: d2f/dx2 + d2f/dy2 + d2f/dz2
                                T new_bM = b0[iM] + nu*( (bxp[iM]-2*b0[iM]+bxn[iM]) + (byp[iM]-2*b0[iM]+byn[iM]) + (bzp[iM]-2*b0[iM]+bzn[iM]) );
                                if (new_bM > COMPLAB_THRD ) {
                                    Array<T,7> g;
                                    plint iXb = iX + vec_offset[iM].x, iYb = iY + vec_offset[iM].y, iZb = iZ + vec_offset[iM].z;
                                    g[0]=(T) (new_bM-1)/4; g[1]=g[2]=g[3]=g[4]=g[5]=g[6]=(T) (new_bM-1)/8;
                                    lattices[iM]->get(iXb,iYb,iZb).setPopulations(g);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulk;
    }
    virtual fdDiffusion3D<T,Descriptor>* clone() const {
        return new fdDiffusion3D<T,Descriptor>(*this);
    }
    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        plint numbM = (length-1)/2;
        for (plint iB=0; iB<numbM; ++iB) {
            modified[iB] = modif::staticVariables;
            modified[iB+numbM] = modif::nothing;
        }
        modified[length-1] = modif::nothing;
    }
private:
    plint nx, ny, nz, length, bdryGap;
    T nu;
};

// update solute diffusivity at a biomass voxel
template<typename T, template<typename U> class Descriptor>
class updateSoluteDynamics3D : public LatticeBoxProcessingFunctional3D<T,Descriptor>
{
public:
    updateSoluteDynamics3D(plint subsNum_, plint bb_, plint solid_, std::vector<plint> pore_, std::vector<T> substrOMEGAinbMass_, std::vector<T> substrOMEGAinPore_)
    : subsNum(subsNum_), bb(bb_), solid(solid_), pore(pore_), substrOMEGAinbMass(substrOMEGAinbMass_), substrOMEGAinPore(substrOMEGAinPore_)
    {}
    // lattices[0~(#ofSubs-1)] = substrate lattices
    // lattices[#ofSubs] = mask lattice
    virtual void process(Box3D domain, std::vector<BlockLattice3D<T,Descriptor>*> lattices) {
        std::vector<Dot3D> vec_offset;
        for (plint iT=0; iT<subsNum+1; ++iT) { vec_offset.push_back(computeRelativeDisplacement(*lattices[0],*lattices[iT])); }
        for (plint iX=domain.x0; iX<=domain.x1; ++iX) {
            plint iXm = iX+vec_offset[subsNum].x;
            for (plint iY=domain.y0; iY<=domain.y1; ++iY) {
                plint iYm = iY+vec_offset[subsNum].y;
                for (plint iZ=domain.z0; iZ<=domain.z1; ++iZ) {
                    plint iZm = iZ+vec_offset[subsNum].z;
                    plint mask = util::roundToInt( lattices[subsNum]->get(iXm,iYm,iZm).computeDensity() );
                    if (mask != bb && mask != solid) {
                        bool poreflag = 0;
                        for (size_t iP=0; iP<pore.size(); ++iP) { if (mask == pore[iP]) {poreflag = 1; break;} }
                        for (plint iS=0; iS<subsNum; ++iS) {
                            plint iXs = iX + vec_offset[iS].x, iYs = iY + vec_offset[iS].y, iZs = iZ + vec_offset[iS].z;
                            T omega = lattices[iS]->get(iXs,iYs,iZs).getDynamics().getOmega();
                            T bMassOmega = substrOMEGAinbMass[iS];
                            if (poreflag == 0 && std::abs(omega-bMassOmega) > COMPLAB_THRD ) {
                                lattices[iS]->get(iXs,iYs,iZs).getDynamics().setOmega(bMassOmega); // pore to bfilm
                            }
                            else if (poreflag == 1 && std::abs(omega-bMassOmega) < COMPLAB_THRD ) {
                                lattices[iS]->get(iXs,iYs,iZs).getDynamics().setOmega(substrOMEGAinPore[iS]); // bfilm to pore
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
    virtual updateSoluteDynamics3D<T,Descriptor>* clone() const {
        return new updateSoluteDynamics3D<T,Descriptor>(*this);
    }
    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        for (plint iS=0; iS<subsNum; ++iS) {
            modified[iS] = modif::dynamicVariables;
        }
        modified[subsNum] = modif::nothing;
    }
private:
    plint subsNum, bb, solid;
    std::vector<plint> pore;
    std::vector<T> substrOMEGAinbMass, substrOMEGAinPore;
};

// update planktonic biomass diffusivity at a biomass voxel
template<typename T, template<typename U> class Descriptor>
class updateBiomassDynamics3D : public LatticeBoxProcessingFunctional3D<T,Descriptor>
{
public:
    updateBiomassDynamics3D(plint bioNum_, plint bb_, plint solid_, std::vector<plint> pore_, std::vector<T> bmassOMEGAinbMass_, std::vector<T> bmassOMEGAinPore_)
    : bioNum(bioNum_), bb(bb_), solid(solid_), pore(pore_), bmassOMEGAinbMass(bmassOMEGAinbMass_), bmassOMEGAinPore(bmassOMEGAinPore_)
    {}
    // lattices[0~(#ofbMs-1)] = planktonic biomass lattices
    // lattices[#ofbMs] = mask lattice
    virtual void process(Box3D domain, std::vector<BlockLattice3D<T,Descriptor>*> lattices) {
        std::vector<Dot3D> vec_offset;
        for (plint iT=0; iT<bioNum+1; ++iT) { vec_offset.push_back(computeRelativeDisplacement(*lattices[0],*lattices[iT])); }
        for (plint iX=domain.x0; iX<=domain.x1; ++iX) {
            plint iXm = iX+vec_offset[bioNum].x;
            for (plint iY=domain.y0; iY<=domain.y1; ++iY) {
                plint iYm = iY+vec_offset[bioNum].y;
                for (plint iZ=domain.z0; iZ<=domain.z1; ++iZ) {
                    plint iZm = iZ+vec_offset[bioNum].z;
                    plint mask = util::roundToInt( lattices[bioNum]->get(iXm,iYm,iZm).computeDensity() );
                    if (mask != bb && mask != solid) {
                        bool poreflag = 0;
                        for (size_t iP=0; iP<pore.size(); ++iP) { if (mask == pore[iP]) {poreflag = 1; break;} }
                        for (plint iB=0; iB<bioNum; ++iB) {
                            plint iXb = iX + vec_offset[iB].x, iYb = iY + vec_offset[iB].y, iZb = iZ + vec_offset[iB].z;
                            T omega = lattices[iB]->get(iXb,iYb,iZb).getDynamics().getOmega();
                            T bMassOmega = bmassOMEGAinbMass[iB];
                            if (poreflag == 0 && std::abs(omega-bMassOmega) > COMPLAB_THRD ) {
                                lattices[iB]->get(iXb,iYb,iZb).getDynamics().setOmega(bMassOmega); // pore to bfilm
                            }
                            else if (poreflag == 1 && std::abs(omega-bMassOmega) < COMPLAB_THRD ) {
                                lattices[iB]->get(iXb,iYb,iZb).getDynamics().setOmega(bmassOMEGAinPore[iB]); // bfilm to pore
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
    virtual updateBiomassDynamics3D<T,Descriptor>* clone() const {
        return new updateBiomassDynamics3D<T,Descriptor>(*this);
    }
    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        for (plint iB=0; iB<bioNum; ++iB) {
            modified[iB] = modif::dynamicVariables;
        }
        modified[bioNum] = modif::nothing;
    }
private:
    plint bioNum, bb, solid;
    std::vector<plint> pore;
    std::vector<T> bmassOMEGAinbMass, bmassOMEGAinPore;
};

// update the flow field
template<typename T1, template<typename U> class Descriptor1, typename T2, template<typename U> class Descriptor2>
class updateNsLatticesDynamics3D : public BoxProcessingFunctional3D_LL<T1,Descriptor1,T2,Descriptor2>
{
public:
    updateNsLatticesDynamics3D(T nsOmega_, T bioX_, std::vector<plint> pore_, plint solid_, plint bb_)
    : nsOmega(nsOmega_), bioX(bioX_), pore(pore_), solid(solid_), bb(bb_)
    {}
    // lattice0 = flow field lattice
    // lattice1 = mask field lattice
    virtual void process(Box3D domain, BlockLattice3D<T1,Descriptor1>& lattice0, BlockLattice3D<T2,Descriptor2>& lattice1) {
        T bioOmega = 1/(bioX*(1/nsOmega-.5)+.5);
        Dot3D offset_12 = computeRelativeDisplacement(lattice0,lattice1);
        for (plint iX0=domain.x0; iX0<=domain.x1; ++iX0) {
            plint iX1 = iX0 + offset_12.x;
            for (plint iY0=domain.y0; iY0<=domain.y1; ++iY0) {
                plint iY1 = iY0 + offset_12.y;
                for (plint iZ0=domain.z0; iZ0<=domain.z1; ++iZ0) {
                    plint iZ1 = iZ0 + offset_12.z;
                    plint mask = util::roundToInt( lattice1.get(iX1,iY1,iZ1).computeDensity() );
                    T currentOmega = lattice0.get(iX0,iY0,iZ0).getDynamics().getOmega();
                    if (mask != bb || mask != solid) {
                        bool poreflag = 0;
                        for (size_t iP=0; iP<pore.size(); ++iP) { if (mask == pore[iP]) {poreflag = 1; break;} }
                        // from pore to biomass
                        if ( poreflag == 0 && std::abs(currentOmega-nsOmega) < COMPLAB_THRD) {
                            if (bioX <= COMPLAB_THRD ) { lattice0.attributeDynamics(iX0, iY0, iZ0, new BounceBack<T1,Descriptor1>() ); }
                            else { lattice0.attributeDynamics(iX0, iY0, iZ0, new IncBGKdynamics<T1,Descriptor1>(bioOmega) ); }
                        }
                        // from biomass to pore
                        else if ( poreflag == 1 && std::abs(currentOmega-nsOmega) > COMPLAB_THRD) {
                            lattice0.attributeDynamics(iX0, iY0, iZ0, new IncBGKdynamics<T1,Descriptor1>(nsOmega) );
                        }
                    }
                }
            }
        }
    }
    virtual updateNsLatticesDynamics3D<T1,Descriptor1,T2,Descriptor2>* clone() const {
        return new updateNsLatticesDynamics3D<T1,Descriptor1,T2,Descriptor2>(*this);
    }
    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulkAndEnvelope;
    }
    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        modified[0] = modif::dataStructure;
        modified[1] = modif::nothing;
    }
private :
    T nsOmega, bioX;
    std::vector<plint> pore;
    plint solid, bb;
};

// redefine age lattice
template<typename T, template<typename U> class Descriptor>
class updateAgeDistance3D : public LatticeBoxProcessingFunctional3D<T,Descriptor>
{
public:
    updateAgeDistance3D(T Bmax_, plint nx_, plint ny_, plint nz_)
    : Bmax(Bmax_), nx(nx_), ny(ny_), nz(nz_)
    {}
    // lattices[0] = age 0 lattices
    // lattices[1] = dist lattices
    // lattices[2] = total biomass lattice
    virtual void process(Box3D domain, std::vector<BlockLattice3D<T,Descriptor>*> lattices) {
        std::vector<Dot3D> vec_offset;
        Dot3D absoluteOffset = lattices[0]->getLocation();
        plint ageLloc = 0, distLloc = 1, bMtLloc = 2;
        for (plint iL=0; iL<3; ++iL) { vec_offset.push_back(computeRelativeDisplacement(*lattices[0],*lattices[iL])); }
        for (plint iX0=domain.x0; iX0<=domain.x1; ++iX0) {
            plint iXb = iX0+vec_offset[bMtLloc].x;
            for (plint iY0=domain.y0; iY0<=domain.y1; ++iY0) {
                plint iYb = iY0+vec_offset[bMtLloc].y;
                for (plint iZ0=domain.z0; iZ0<=domain.z1; ++iZ0) {
                    plint iZb = iZ0+vec_offset[bMtLloc].z;
                    T B = lattices[bMtLloc]->get(iXb,iYb,iZb).computeDensity();
                    if (B > COMPLAB_THRD ) {
                        plint absX = iX0 + absoluteOffset.x, absY = iY0 + absoluteOffset.y, absZ = iZ0 + absoluteOffset.z;
                        plint iXa = iX0 + vec_offset[ageLloc].x, iYa = iY0 + vec_offset[ageLloc].y, iZa = iZ0 + vec_offset[ageLloc].z;
                        plint iXd = iX0 + vec_offset[distLloc].x, iYd = iY0 + vec_offset[distLloc].y, iZd = iZ0 + vec_offset[distLloc].z;
                        std::vector<plint> delXYZ; plint nbrs=0;
                        
                        // Determine neighbors based on boundary position (3D version)
                        bool atXmin = (absX == 0);
                        bool atXmax = (absX == nx-1);
                        bool atYmin = (absY == 0);
                        bool atYmax = (absY == ny-1);
                        bool atZmin = (absZ == 0);
                        bool atZmax = (absZ == nz-1);
                        
                        // Add valid neighbors
                        if (!atXmax) { delXYZ.push_back(1); delXYZ.push_back(0); delXYZ.push_back(0); ++nbrs; }
                        if (!atXmin) { delXYZ.push_back(-1); delXYZ.push_back(0); delXYZ.push_back(0); ++nbrs; }
                        if (!atYmax) { delXYZ.push_back(0); delXYZ.push_back(1); delXYZ.push_back(0); ++nbrs; }
                        if (!atYmin) { delXYZ.push_back(0); delXYZ.push_back(-1); delXYZ.push_back(0); ++nbrs; }
                        if (!atZmax) { delXYZ.push_back(0); delXYZ.push_back(0); delXYZ.push_back(1); ++nbrs; }
                        if (!atZmin) { delXYZ.push_back(0); delXYZ.push_back(0); delXYZ.push_back(-1); ++nbrs; }

                        std::vector<plint> del_iX, del_iY, del_iZ;
                        for (plint iT=0; iT<nbrs; ++iT) {
                            plint delx = delXYZ[iT*3], dely = delXYZ[iT*3+1], delz = delXYZ[iT*3+2];
                            plint dist = util::roundToInt( lattices[distLloc]->get(iXd+delx,iYd+dely,iZd+delz).computeDensity() );
                            if (dist > 0) { del_iX.push_back(delx); del_iY.push_back(dely); del_iZ.push_back(delz); }
                        }
                        T newAge = 0; bool updateflag = 1;
                        plint age = util::roundToInt( lattices[ageLloc]->get(iXa,iYa,iZa).computeDensity() );
                        if (age==0 ) { newAge = 1; }
                        else if ( age==1 && (B-Bmax)>-COMPLAB_THRD) {
                            for (size_t iT=0; iT<del_iX.size(); ++iT) {
                                plint delx = del_iX[iT], dely = del_iY[iT], delz = del_iZ[iT];
                                plint nbrAge = util::roundToInt( lattices[ageLloc]->get(iXa+delx,iYa+dely,iZa+delz).computeDensity() );
                                plint nbrDist = util::roundToInt( lattices[distLloc]->get(iXd+delx,iYd+dely,iZd+delz).computeDensity() );
                                if ( nbrDist > 0 && nbrAge == 0 ) { updateflag = 0; break; }
                            }
                            if (updateflag == 1) { newAge = 2; }
                        }
                        else {
                            plint count = 0;
                            for (size_t iT=0; iT<del_iX.size(); ++iT) {
                                plint delx = del_iX[iT], dely = del_iY[iT], delz = del_iZ[iT];
                                plint nbrAge = util::roundToInt( lattices[ageLloc]->get(iXa+delx,iYa+dely,iZa+delz).computeDensity() );
                                T nbrB = lattices[bMtLloc]->get(iXb+delx,iYb+dely,iZb+delz).computeDensity();
                                if ( nbrAge >= age && (nbrB-Bmax)>-COMPLAB_THRD) { ++count; }
                            }
                            if ((size_t)count == del_iX.size()) { newAge = (T) (age+1); }
                            else { updateflag = 0; }
                        }
                        if (updateflag == 1) {
                            Array<T,7> g;
                            g[0]=(T) (newAge-1)/4; g[1]=g[2]=g[3]=g[4]=g[5]=g[6]=(T) (newAge-1)/8;
                            lattices[ageLloc]->get(iXa,iYa,iZa).setPopulations(g);
                        }
                    }
                }
            }
        }
    }
    virtual BlockDomain::DomainT appliesTo() const {
        return BlockDomain::bulk;
    }
    virtual updateAgeDistance3D<T,Descriptor>* clone() const {
        return new updateAgeDistance3D<T,Descriptor>(*this);
    }
    void getTypeOfModification(std::vector<modif::ModifT>& modified) const {
        modified[0] = modif::staticVariables;
        modified[1] = modif::nothing;
        modified[2] = modif::nothing;
    }
private:
    T Bmax;
    plint nx, ny, nz;
};

#endif // COMPLAB3D_PROCESSORS_PART2_HH
