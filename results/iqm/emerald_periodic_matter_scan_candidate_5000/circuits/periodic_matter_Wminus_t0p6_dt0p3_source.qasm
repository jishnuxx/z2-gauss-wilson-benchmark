OPENQASM 2.0;
include "qelib1.inc";
gate gate_PauliEvolution(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.15) q0; }
gate gate_PauliEvolution_5050589904(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.15) q1; }
gate gate_PauliEvolution_5050590240(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.15) q2; }
gate gate_PauliEvolution_5050590624(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.15) q3; }
gate gate_PauliEvolution_5050590960(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.3) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_5050591248(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.3) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_5050591728(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.3) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_5050591440(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.3) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_5050592592(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.3) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_5050592400(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.3) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_5050592304(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.3) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_5050036304(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.3) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
gate gate_PauliEvolution_5050360672(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.15) q1; }
gate gate_PauliEvolution_5050014304(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.15) q2; }
gate gate_PauliEvolution_5050014832(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.15) q3; }
gate gate_PauliEvolution_5050023616(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.3) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_5050012576(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.3) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_5050019440(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.3) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_5050019968(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.3) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_5050019824(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.3) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_5049943920(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.3) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_5049957840(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.3) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_5049946800(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.3) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
qreg q[8];
creg c[4];
x q[0];
x q[1];
h q[4];
cx q[4],q[5];
cx q[4],q[6];
cx q[4],q[7];
x q[5];
x q[6];
x q[7];
z q[4];
gate_PauliEvolution(-0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050589904(0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050590240(-0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050590624(0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050590960(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050591248(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050591728(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050591440(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050592592(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050592400(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050592304(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050036304(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution(-0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050360672(0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050014304(-0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050014832(0.075) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050023616(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050012576(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050019440(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050019968(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050019824(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5049943920(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5049957840(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5049946800(-0.15) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];