OPENQASM 2.0;
include "qelib1.inc";
gate gate_PauliEvolution(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.25) q0; }
gate gate_PauliEvolution_4649361072(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q1; }
gate gate_PauliEvolution_4649364672(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.25) q2; }
gate gate_PauliEvolution_4649365104(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q3; }
gate gate_PauliEvolution_4649365440(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_4649365680(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_4649366208(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_4649356032(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_4649204768(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_4649205536(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_4649366064(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_4649366544(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
gate gate_PauliEvolution_4649365344(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q1; }
gate gate_PauliEvolution_4649365008(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(-0.25) q2; }
gate gate_PauliEvolution_4649362800(param0) q0,q1,q2,q3,q4,q5,q6,q7 { rz(0.25) q3; }
gate gate_PauliEvolution_4649363472(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; h q0; h q1; h q4; }
gate gate_PauliEvolution_4649356752(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q1; h q4; cx q4,q1; cx q1,q0; rz(-0.5) q0; cx q1,q0; cx q4,q1; sxdg q0; sxdg q1; h q4; }
gate gate_PauliEvolution_4649362176(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q1; h q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; h q1; h q2; h q5; }
gate gate_PauliEvolution_4649360832(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q1; sx q2; h q5; cx q5,q2; cx q2,q1; rz(-0.5) q1; cx q2,q1; cx q5,q2; sxdg q1; sxdg q2; h q5; }
gate gate_PauliEvolution_4649360880(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q2; h q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; h q2; h q3; h q6; }
gate gate_PauliEvolution_4649358624(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q2; sx q3; h q6; cx q6,q3; cx q3,q2; rz(-0.5) q2; cx q3,q2; cx q6,q3; sxdg q2; sxdg q3; h q6; }
gate gate_PauliEvolution_4649363136(param0) q0,q1,q2,q3,q4,q5,q6,q7 { h q0; h q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; h q0; h q3; h q7; }
gate gate_PauliEvolution_4649366640(param0) q0,q1,q2,q3,q4,q5,q6,q7 { sx q0; sx q3; h q7; cx q7,q3; cx q3,q0; rz(-0.5) q0; cx q3,q0; cx q7,q3; sxdg q0; sxdg q3; h q7; }
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
gate_PauliEvolution_4649361072(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649364672(-0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649365104(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649365440(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649365680(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649366208(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649356032(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649204768(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649205536(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649366064(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649366544(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution(-0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649365344(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649365008(-0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649362800(0.125) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649363472(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649356752(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649362176(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649360832(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649360880(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649358624(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649363136(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
gate_PauliEvolution_4649366640(-0.25) q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];