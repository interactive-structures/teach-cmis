

//////////////////////////////////
// libigl example 403 with hand //
//////////////////////////////////


#include <igl/boundary_conditions.h>
#include <igl/colon.h>
#include <igl/column_to_quats.h>
#include <igl/directed_edge_parents.h>
#include <igl/forward_kinematics.h>
#include <igl/jet.h>
#include <igl/lbs_matrix.h>
#include <igl/deform_skeleton.h>
#include <igl/readDMAT.h>
#include <igl/readMESH.h>
#include <igl/readTGF.h>
#include <igl/opengl/glfw/Viewer.h>
#include <igl/bbw.h>

#include <Eigen/Geometry>
#include <Eigen/StdVector>
#include <vector>
#include <algorithm>
#include <iostream>

#include "model_path.h"


namespace mesh_smoothing {
    int inner_main(int argc, char* argv[]);
}
int main(int argc, char* argv[]) {
    try {
        return mesh_smoothing::inner_main(argc, argv);
    }
    catch (char const* x) {
        std::cerr << "Error: " << std::string(x) << std::endl;
    }
    return 1;
}


namespace mesh_smoothing {



    typedef
        std::vector<Eigen::Quaterniond, Eigen::aligned_allocator<Eigen::Quaterniond> >
        RotationList;

    const Eigen::RowVector3d sea_green(70. / 255., 252. / 255., 167. / 255.);
    int selected = 0;
    Eigen::MatrixXd V, W, U, C, M;
    Eigen::MatrixXi T, F, BE;
    Eigen::VectorXi P;
    RotationList pose;
    double anim_t = 1.0;
    double anim_t_dir = -0.03;

    bool pre_draw(igl::opengl::glfw::Viewer& viewer)
    {
        using namespace Eigen;
        using namespace std;
        if (viewer.core().is_animating)
        {
            // Interpolate pose and identity
            RotationList anim_pose(pose.size());
            for (int e = 0; e < pose.size(); e++)
            {
                anim_pose[e] = pose[e].slerp(anim_t, Quaterniond::Identity());
            }
            // Propagate relative rotations via FK to retrieve absolute transformations
            RotationList vQ;
            vector<Vector3d> vT;
            igl::forward_kinematics(C, BE, P, anim_pose, vQ, vT);
            const int dim = C.cols();
            MatrixXd T(BE.rows() * (dim + 1), dim);
            for (int e = 0; e < BE.rows(); e++)
            {
                Affine3d a = Affine3d::Identity();
                a.translate(vT[e]);
                a.rotate(vQ[e]);
                T.block(e * (dim + 1), 0, dim + 1, dim) =
                    a.matrix().transpose().block(0, 0, dim + 1, dim);
            }
            // Compute deformation via LBS as matrix multiplication
            U = M * T;

            // Also deform skeleton edges
            MatrixXd CT;
            MatrixXi BET;
            igl::deform_skeleton(C, BE, T, CT, BET);

            viewer.data().set_vertices(U);
            viewer.data().set_edges(CT, BET, sea_green);
            viewer.data().compute_normals();
            anim_t += anim_t_dir;
            anim_t_dir *= (anim_t >= 1.0 || anim_t <= 0.0 ? -1.0 : 1.0);
        }
        return false;
    }

    bool key_down(igl::opengl::glfw::Viewer& viewer, unsigned char key, int mods)
    {
        switch (key)
        {
        case ' ':
            viewer.core().is_animating = !viewer.core().is_animating;
            break;
        case '.':
            selected++;
            selected = std::min(std::max(selected, 0), (int)W.cols() - 1);
            viewer.data().set_data(W.col(selected));
            break;
        case ',':
            selected--;
            selected = std::min(std::max(selected, 0), (int)W.cols() - 1);
            viewer.data().set_data(W.col(selected));
            break;
        }
        return true;
    }

    int inner_main(int argc, char* argv[])
    {
        using namespace Eigen;
        using namespace std;
        igl::readMESH(PathHelper::get_folder_path(__FILE__) + "/../../models/hand.mesh", V, T, F);
        U = V;
        igl::readTGF(PathHelper::get_folder_path(__FILE__) + "/../../models/hand.tgf", C, BE);
        // retrieve parents for forward kinematics
        igl::directed_edge_parents(BE, P);

        // Read pose as matrix of quaternions per row
        MatrixXd Q;
        igl::readDMAT(PathHelper::get_folder_path(__FILE__) + "/../../models/hand-pose.dmat", Q);
        igl::column_to_quats(Q, pose);
        assert(pose.size() == BE.rows());

        // List of boundary indices (aka fixed value indices into VV)
        VectorXi b;
        // List of boundary conditions of each weight function
        MatrixXd bc;
        igl::boundary_conditions(V, T, C, VectorXi(), BE, MatrixXi(), b, bc);
        // Inputs:
//   V  #V by dim list of domain vertices
//   Ele  #Ele by simplex-size list of simplex indices
//   C  #C by dim list of handle positions
//   P  #P by 1 list of point handle indices into C
//   BE  #BE by 2 list of bone edge indices into C
//   CE  #CE by 2 list of cage edge indices into *P*
// 
        // compute BBW weights matrix
        igl::BBWData bbw_data;
        // only a few iterations for sake of demo
        bbw_data.active_set_params.max_iter = 8;
        bbw_data.verbosity = 2;
        if (!igl::bbw(V, T, b, bc, bbw_data, W))
        {
            return EXIT_FAILURE;
        }

        //MatrixXd Vsurf = V.topLeftCorner(F.maxCoeff()+1,V.cols());
        //MatrixXd Wsurf;
        //if(!igl::bone_heat(Vsurf,F,C,VectorXi(),BE,MatrixXi(),Wsurf))
        //{
        //  return false;
        //}
        //W.setConstant(V.rows(),Wsurf.cols(),1);
        //W.topLeftCorner(Wsurf.rows(),Wsurf.cols()) = Wsurf = Wsurf = Wsurf = Wsurf;

        // Normalize weights to sum to one
        W = (W.array().colwise() / W.array().rowwise().sum()).eval();
        // precompute linear blend skinning matrix
        igl::lbs_matrix(V, W, M);

        // Plot the mesh with pseudocolors
        igl::opengl::glfw::Viewer viewer;
        viewer.data().set_mesh(U, F);
        viewer.data().set_data(W.col(selected));
        viewer.data().set_edges(C, BE, sea_green);
        viewer.data().show_lines = false;
        viewer.data().show_overlay_depth = false;
        viewer.data().line_width = 1;
        viewer.callback_pre_draw = &pre_draw;
        viewer.callback_key_down = &key_down;
        viewer.core().is_animating = false;
        viewer.core().animation_max_fps = 30.;
        cout <<
            "Press '.' to show next weight function." << endl <<
            "Press ',' to show previous weight function." << endl <<
            "Press [space] to toggle animation." << endl;
        viewer.launch();
        return EXIT_SUCCESS;
    }
}
