% ============================================================================
% agente/templo.lp — PARTE 3: el conocimiento del templo en ASP (clingo).
%
% El motor (engine/asp.py) añade estos HECHOS según lo que va observando el
% agente:
%   tamano(N).               el templo es N x N
%   num_fosos(K).            el plano indica cuántos fosos hay
%   visitada(F,C).           el arqueólogo ha estado (vivo) en (F,C)
%   percibe(P,F,C).          en (F,C) se percibe P ∈ {corriente, siseo, luz}
%   no_percibe(P,F,C).       en (F,C) NO se percibe P
%   antorcha(F,C,si).        se lanzó la antorcha a (F,C) y se oyó un chillido
%   antorcha(F,C,no).        se lanzó la antorcha a (F,C) y no pasó nada
%   huida.                   la serpiente ha huido (ya no es un peligro)
%   no_es_salida(F,C).       se intentó SALIR en (F,C) y no era la salida
%
% Predicados OBLIGATORIOS (con su #show): foso/2, serpiente/2, salida/2, segura/2.
% El motor pregunta a clingo qué átomos son ciertos en TODOS los modelos
% (consecuencias cautas = lo que se puede deducir) y en ALGUNO (bravas = lo
% que es posible).
% ============================================================================

% --- Dominio -----------------------------------------------------------------
celda(F,C) :- tamano(N), F = 1..N, C = 1..N.
ady(F,C,X,Y) :- celda(F,C), celda(X,Y), |F-X| + |C-Y| = 1.

% --- TODO 1: lo que no sabemos (dónde está cada cosa) -------------------------
% Exactamente K fosos (num_fosos(K)), una serpiente y una salida, en celdas
% distintas.  Pista: reglas de elección con cardinalidad  L { a(X) : b(X) } U.


% --- TODO 2: qué produce cada cosa ---------------------------------------------
% Definid cuándo HAY corriente, siseo y luz en una celda.
% Sugerencia: un predicado hay(P,F,C) con P ∈ {corriente, siseo, luz}.


% --- TODO 3: los modelos deben coincidir con lo observado -----------------------
% Restricciones de integridad ( :- ... ) con percibe/3, no_percibe/3, visitada/2,
% antorcha/3, huida y no_es_salida/2.


% --- TODO 4: celdas seguras ------------------------------------------------------
% segura(F,C): la celda no tiene foso ni (si no ha huido) serpiente.


#show foso/2.
#show serpiente/2.
#show salida/2.
#show segura/2.
