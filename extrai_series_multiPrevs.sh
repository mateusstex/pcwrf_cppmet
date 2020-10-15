#!/bin/bash

for diretorio in `ls -d /media/mateus/PCWRF_CPMET/pcwrf_saidas/*`
do
    echo ''
    echo "Extraindo dados de $diretorio ..."
    time python extrai_series_pcwrf_inmet.py $diretorio
    if [ $? != 0 ]   # se houver problema em uma execução do script Python, para tudo!
    then
	echo 'Erro ao extrair dados. Verificar problemas!'
	exit
    fi
    echo ''
    echo ''
    
done
