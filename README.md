Ce projet à été organisé élément par élément (méthode agile). Cela signifie que :
      - les fichiers test*.py contiennent les implémentations basique des élément
      - My_useless_grover.py est la V1. Il retrouve un motif donner en entrée (on lui donne 306, il ressort 306)
      - My_grover.py est sa V2. Il retrouve également un motif dans une liste (retrouve 306 dans une liste).
      - My_grover_db.py est sa V3. Il prend en entrée une base de donnée, vectorise les blagues, et retrouve une blague en fonction de sa question.
      - My_grover_db_IBMExecution.py est sa V3. La différence est que l'appareil exécutera le circuits quantique sur les serveurs d'IBM.

Cependant, Je n'ai pas py tester la V3 de ce projet, car je n'ai pas suffisamment de ram, même en l'exécutant sur les serveurs d'IBM. Etant donné que chacun des éléments fonctionne individuellement, Il devrait fonctionner.

Les différents histogrammes représentent les résultats a différents moments de l'execution. Lors de l'initialisation (*_start), et a la fin (sans le *_start).

Enfin, voici un lien vers la db : <https://www.kaggle.com/datasets/jiriroz/qa-jokes>

Note : \* fait référence a la commande ls, signifiant "tout ce qui contiens". Par exemple test\*.py signifiant tout ce qui commence par test et fini par .py
