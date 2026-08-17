OPENQASM 2.0;
include "qelib1.inc";
gate gate_PauliEvolution(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.2) q0; }
gate gate_PauliEvolution_5050011376(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.2) q1; }
gate gate_PauliEvolution_5050021168(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.2) q2; }
gate gate_PauliEvolution_4996441840(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.2) q3; }
gate gate_PauliEvolution_5049942240(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.4) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_5049958176(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.4) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_5050587216(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.4) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_5050582608(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.4) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_5050582272(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.4) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_5050581840(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.4) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_5050584000(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.4) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_5050593072(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.4) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
gate gate_PauliEvolution_5050595664(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.2) q1; }
gate gate_PauliEvolution_5050595856(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.2) q2; }
gate gate_PauliEvolution_5050596144(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.2) q3; }
gate gate_PauliEvolution_5050596528(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.4) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_5050595712(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.4) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_5050596960(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.4) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_5050597104(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.4) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_5050794400(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.4) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_5050794208(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.4) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_5050794928(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.4) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_5050597296(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.4) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
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
gate_PauliEvolution(-0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050011376(0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050021168(-0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4996441840(0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5049942240(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5049958176(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050587216(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050582608(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050582272(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050581840(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050584000(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050593072(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution(-0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050595664(0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050595856(-0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050596144(0.1) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050596528(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050595712(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050596960(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050597104(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050794400(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050794208(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050794928(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_5050597296(-0.2) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];