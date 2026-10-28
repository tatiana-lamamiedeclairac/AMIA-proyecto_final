% ============================================================================
% agente/expedicion.lp — PARTE 4: el reparto de la expedición en ASP (clingo).
%
% El motor (engine/expedicion.py) añade estos HECHOS:
%   arqueologo(indy).  arqueologo(lara).
%   equipo(indy,botiquin).  equipo(lara,pico).
%   perdido(p1).  perdido(p2).  ...      los perdidos que hay que rescatar
%   herido(P).                           P está herido: necesita botiquín
%   atrapado(P).                         P está atrapado: necesita pico
%   capacidad(K).                        cada arqueólogo saca como mucho a K
%
% Predicado OBLIGATORIO (con su #show): rescata/2, rescata(A,P) = «el
% arqueólogo A rescata al perdido P».
% Cada MODELO (answer set) es un reparto válido.  El motor los pide TODOS y
% vuestro coordinador.py elige el mejor con A*.
%
% Probadlo en la terminal:   python -m clingo agente/expedicion.lp mapas/expedicion_roles.lp 0
% ============================================================================

% --- TODO 1: cada perdido lo rescata exactamente UN arqueólogo -----------------
% Pista: como en los puzzles de clase, { a(X,Y) : b(Y) } = 1 :- c(X).


% --- TODO 2: a un herido solo lo puede rescatar quien lleva botiquín -----------
% Pista: una restricción de integridad  :- ... , not equipo(A,botiquin).


% --- TODO 3: a un atrapado solo lo puede rescatar quien lleva pico -------------


% --- TODO 4: nadie rescata a más de capacidad(K) perdidos ----------------------
% Pista: como num_fosos en templo.lp, una cardinalidad  L { ... }  también puede
% ir en el CUERPO de una restricción: «es imposible que A rescate a K+1 o más».


% --- TODO 5: es una expedición en equipo: los dos arqueólogos trabajan ---------
% Pista: definid trabaja(A) y prohibid que un arqueólogo no trabaje.


#show rescata/2.
