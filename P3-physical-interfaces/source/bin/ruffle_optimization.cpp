#include <igl/opengl/glfw/Viewer.h>
#include <igl/opengl/glfw/imgui/ImGuiMenu.h>
#include <igl/opengl/glfw/imgui/ImGuiHelpers.h>
#include <igl/file_dialog_open.h>
#include <igl/file_dialog_save.h>

#include "common/common.h"
#include "common/imgui.h"

#include "ruffle/ruffle.h"
#include "simulation/verlet.h"
#include "simulation/lbfgs.h"

#include "optimization/target_shape.h"
#include "optimization/particle_swarm.h"
#include "optimization/heuristic.h"

#include "visualization/visualization.h"

#include "output/create_svg.h"

#include <unordered_map>

#include <chrono>

namespace ruffles {
	int inner_main(int argc, char *argv[]);
}
int main(int argc, char *argv[]) {
	try {
		return ruffles::inner_main(argc, argv);
	} catch (char const *x) {
		std::cerr << "Error: " << std::string(x) << std::endl;
	}
	return 1;
}


namespace ruffles {

using simulation::SimulationMesh;
using visualization::Visualization;

Polygon createTargetRectangle(double w, double h) {
	Polygon polygon;

	double x_offset = -w * 0.9 * 0.15;
	double y_offset = 0.;

	polygon.push_back(Point(0. + x_offset, 0. + y_offset));
	polygon.push_back(Point(w + x_offset,  0. + y_offset));
	polygon.push_back(Point(w + x_offset,  h + y_offset));
	polygon.push_back(Point(0. + x_offset, h + y_offset));

	return polygon;
}

Polygon createTargetCircle(double radius, double startAngle = 0.0, double endAngle = 2 * M_PI) {
	int n = 32;
	double angleIncrement = (endAngle - startAngle) / (n - 1);
	Polygon polygon;

	for (int i = 0; i < n; ++i) {
		double angle = startAngle + i * angleIncrement;
		double x = radius * std::cos(angle) + radius*0.75;
		double y = radius * std::sin(angle) + radius;
		polygon.push_back(Point(x, y));
	}
	return polygon;
}

Polygon createTargetSemiCircle(double radius) {
	int n = 32;
	double startAngle = 0.0;
	double endAngle = M_PI;
	double angleIncrement = (endAngle - startAngle) / (n - 1);
	Polygon polygon;

	for (int i = 0; i < n; ++i) {
		double angle = startAngle + i * angleIncrement;
		double x = radius * std::cos(angle) + radius*0.75;
		double y = radius * std::sin(angle);
		polygon.push_back(Point(x, y));
	}
	return polygon;
}

int inner_main(int argc, char *argv[]) {
	(void)argc;
	(void)argv;


	//Polygon polygon = createTargetCircle(5.0); 
	Polygon polygon = createTargetSemiCircle(6.0);
	//Polygon polygon = createTargetRectangle(10, 10);

	double target_width = polygon.bbox().xmax() - polygon.bbox().xmin();
	double target_height = polygon.bbox().ymax() - polygon.bbox().ymin();
	int num_ruffles = int(round(target_height / 3.));
	Ruffle ruffle = Ruffle::create_ruffle_stack(num_ruffles, target_height/num_ruffles*0.99, target_width*0.8, 0.5);
	for (auto& vx : ruffle.simulation_mesh.vertices) {
		vx.width = 5.;
	}

	ruffle.simulation_mesh.generate_air_mesh();
	ruffle.simulator.reset(new simulation::LBFGS(ruffle.simulation_mesh));
	ruffle.simulation_mesh.lambda_air_mesh = 1e9;
	ruffle.simulation_mesh.update_vertex_mass();

	ruffle.update_simulation_mesh();
	//ruffle.physics_solve();

	optimization::TargetShape target(polygon);
	optimization::Heuristic heuristic(target);

	igl::opengl::glfw::Viewer viewer;
	viewer.core().background_color.setOnes();
	viewer.core().set_rotation_type(igl::opengl::ViewerCore::ROTATION_TYPE_TRACKBALL);
	viewer.resize(1600, 1400);


	Visualization vis;
	auto update_visualization = [&]() {
		vis.clear();

		auto &mesh = ruffle.simulation_mesh;
		std::unordered_map<listref<SimulationMesh::Vertex>, int, listref_hash<SimulationMesh::Vertex>> indices;

		//Vector3(0.8, 0.8, 0.8);
		int i = 0;
		for (auto it = mesh.vertices.begin(); it != mesh.vertices.end(); ++it) {
			Vector2 pos = mesh.get_vertex_position(*it);
			vis.push_vertex((Vector3() << pos, -0.5*it->width).finished());
			vis.push_vertex((Vector3() << pos,  0.5*it->width).finished());
			indices.insert({it, i});
			i++;
		}

		auto color = Vector3(0.8, 0.8, 0.8);
		for (auto seg : mesh.segments) {
			int a = indices[seg.start];
			int b = indices[seg.end];

			vis.push_face(2*a, 2*b, 2*b+1, color);
			vis.push_face(2*b+1, 2*a+1, 2*a, color);
		}

		color = Vector3(0.9, 0.9, 0.55);
		for (auto it = mesh.air_mesh.cdt.finite_faces_begin(); it != mesh.air_mesh.cdt.finite_faces_end(); ++it) {
			int a = it->vertex(0)->info();
			int b = it->vertex(1)->info();
			int c = it->vertex(2)->info();

			vis.push_face(2*a,2*b,2*c, color);
		}

		
		color = Vector3(0.5, 0.7, 0.9);
		int n_old = vis.nv;
		for (int i = 0; i < target.V.rows(); ++i) {
			vis.push_vertex(target.V.row(i).transpose());
		}
		for (int i = 0; i < target.F.rows(); ++i) {
			auto tri = target.F.row(i).array() + n_old;
			vis.push_face(tri(0), tri(1), tri(2), color);
		}

		vis.compress();

		viewer.data().clear();
		viewer.data().clear_labels();

		// draw coordinate indicator
		const auto coordinate_indicator = Eigen::MatrixXd::Identity(3, 3);
		viewer.data().add_edges(Eigen::MatrixXd::Zero(3, 3), coordinate_indicator * 2, coordinate_indicator);

		i = 0;
		for (auto it = mesh.vertices.begin(); it != mesh.vertices.end(); ++it) {
			Vector2 pos = mesh.get_vertex_position(*it);
			viewer.data().add_label((Vector3() << pos, 0.).finished().cast<double>(), to_string(i));
			i++;
		}

		viewer.data().set_mesh(vis.V.cast<double>(), vis.F);
		viewer.data().set_colors(vis.C.cast<double>());

	};
	update_visualization();

	igl::opengl::glfw::imgui::ImGuiMenu menu;
	viewer.plugins.push_back(&menu);
	menu.callback_draw_viewer_menu = [&]() {
		menu.draw_viewer_menu();

		if (ImGui::CollapsingHeader("Ruffle optimization", ImGuiTreeNodeFlags_DefaultOpen)) {
			
			ImGui::Text("Simulation:");
			ImGui::Separator();

			ImGui::InputReal("global stiffness", &ruffle.simulation_mesh.k_global);
			ImGui::InputReal("bending stiffness", &ruffle.simulation_mesh.k_bend);
			ImGui::InputReal("density", &ruffle.simulation_mesh.density);
			ImGui::InputReal("membrane weight", &ruffle.simulation_mesh.lambda_membrane);
			ImGui::InputReal("collision weight", &ruffle.simulation_mesh.lambda_air_mesh);
			ImGui::Text("Current Energy: %f", ruffle.simulation_mesh.energy_sum);
			
			if (ImGui::Button("Step optimization")) {
				heuristic.step(ruffle);
				update_visualization();
			}
			if (ImGui::Button("Reset simulation")) {
				ruffle.simulator->reset(ruffle.simulation_mesh);
			}
			if (ImGui::Button("Solve physics")) {
				ruffle.physics_solve();
				update_visualization();
			}


			ImGui::Text("Output:");
			ImGui::Separator();

			if (ImGui::Button("Intersect cylinder H")) {
				for (auto& vx : ruffle.simulation_mesh.vertices) {
					Vector2 xy = ruffle.simulation_mesh.get_vertex_position(vx);
					real dy = xy.y() - 5.;
					real w = 0.;
					if (dy * dy < 5. * 5.) {
						w = 2. * sqrt(5. * 5. - dy * dy);
					}
					w = max(0.1, w);
					vx.width = w;
				}
				update_visualization();
			}
			if (ImGui::Button("Intersect cylinder V")) {
				for (auto& vx : ruffle.simulation_mesh.vertices) {
					Vector2 xy = ruffle.simulation_mesh.get_vertex_position(vx);
					real dy = xy.x() - 3.;
					real w = 0.;
					if (dy * dy < 5. * 5.) {
						w = 2. * sqrt(5. * 5. - dy * dy);
					}
					w = max(0.1, w);
					vx.width = w;
				}
				update_visualization();
			}

			if (ImGui::Button("Export SVG")) {
				auto svg = create_svg(ruffle);
				svg->SaveFile("/tmp/test.svg");
			}
		}
	};

	viewer.launch();
	return 0;
}
}
