OPENQASM 2.0;
include "qelib1.inc";
gate gate_PauliEvolution(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.25) q0; }
gate gate_PauliEvolution_4602453104(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q1; }
gate gate_PauliEvolution_4602453440(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.25) q2; }
gate gate_PauliEvolution_4602453824(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q3; }
gate gate_PauliEvolution_4602454160(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_4602454496(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_4602454448(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_4602313568(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_4602314000(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_4602311408(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_4602305840(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_4602310304(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
gate gate_PauliEvolution_4602313472(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q1; }
gate gate_PauliEvolution_4602454112(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.25) q2; }
gate gate_PauliEvolution_4602454832(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q3; }
gate gate_PauliEvolution_4602453536(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_4602452384(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_4602451856(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_4602446864(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_4602452240(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_4602451904(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_4602454352(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_4602455456(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
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
gate_PauliEvolution(-0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602453104(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602453440(-0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602453824(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602454160(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602454496(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602454448(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602313568(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602314000(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602311408(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602305840(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602310304(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution(-0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602313472(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602454112(-0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602454832(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602453536(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602452384(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602451856(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602446864(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602452240(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602451904(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602454352(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4602455456(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];