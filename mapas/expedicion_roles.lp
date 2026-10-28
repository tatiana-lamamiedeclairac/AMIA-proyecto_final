% Hechos de mapas/expedicion_roles.txt (los mismos que añade el motor).
% Probad:  python -m clingo agente/expedicion.lp mapas/expedicion_roles.lp 0
%
%   p1 está en (1, 6)
%   p2 está en (3, 1)
%   p3 está en (3, 2)
%   p4 está en (5, 3)
%   p5 está en (6, 6)
arqueologo(indy).
arqueologo(lara).
equipo(indy,botiquin).
equipo(lara,pico).
perdido(p1).
atrapado(p1).
perdido(p2).
perdido(p3).
perdido(p4).
perdido(p5).
herido(p5).
capacidad(3).
