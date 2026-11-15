import numpy as np, itertools
P = np.array([[0,0,0],[1,0,0],[0.5,np.sqrt(3)/2,0],[0.5,np.sqrt(3)/6,np.sqrt(6)/3]])
names = ["W","C","M","K"]
g = P.mean(0); R = np.linalg.norm(P[0]-g)
E = [np.linalg.norm(P[i]-P[j]) for i,j in itertools.combinations(range(4),2)]
area = np.sqrt(3)*E[0]**2
vol = abs(np.linalg.det(np.vstack([P[1]-P[0],P[2]-P[0],P[3]-P[0]])))/6
cos_dih = 1/3
print("=== CONVENTION A (PDF & paper Eq.5): vertex W at origin, |C|=|M|=|K|=1 ===")
print("edge length:", round(E[0],6), "(all edges equal:", all(abs(x-E[0])<1e-9 for x in E), ")")
print("centroid g =", np.round(g,6), "| circumradius R = ||g|| =", round(R,6), "= sqrt(6)/4 =", round(np.sqrt(6)/4,6))
print("dot products among {C,M,K} from origin:", round(P[1]@P[2],6), round(P[1]@P[3],6), round(P[2]@P[3],6), "-> angle 60 deg")
print("volume V =", round(vol,6), "sqrt(2)/12 =", round(np.sqrt(2)/12,6))
print("surface area =", round(area,6), "sqrt(3) =", round(np.sqrt(3),6))
print("dihedral angle =", round(np.degrees(np.arccos(1/3)),4), "deg; angle at centroid between vertex vectors =",
      round(np.degrees(np.arccos((P[1]-g)@(P[2]-g)/R**2)),4), "deg")
print("inradius r = 3V/area =", round(3*vol/area,6), "= sqrt(6)/12 =", round(np.sqrt(6)/12,6))
V = np.array([p-g for p in P])
print("\n=== CONVENTION B (centred, needed for paper Eq.1): v_i = P_i - g ===")
print("||v_i|| =", round(np.linalg.norm(V[0]),6), "= sqrt(3/8) =", round(np.sqrt(3/8),6))
print("v_i . v_j =", round(V[0]@V[1],6), "(-1/8), NOT -1/3 as Eq.(1) states")
Vn = V/np.linalg.norm(V[0])
print("after normalisation: ||v_i||=1, v_i.v_j =", round(Vn[0]@Vn[1],6), "(= -1/3 ✓), edge =",
      round(np.linalg.norm(Vn[0]-Vn[1]),6), "= sqrt(8/3) =", round(np.sqrt(8/3),6))
