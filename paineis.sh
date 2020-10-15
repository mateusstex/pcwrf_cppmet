#!/bin/bash

# Script BASH para montagem dos paineis usando o comando montage do ImageMagick
#
# As strings estão todas entre aspas duplas, pois apenas com elas o valor de
# variáveis é usado em uma string e em substituição de comando
#
# O script usa matemática de data disponível no comando date para poder
# avançar a data, cf. https://www.linuxjournal.com/content/doing-date-math-command-line-part-i
#
# MODO DE USO:
#
#       ./paineis.sh AAAA MM DD
#
#   onde
#        AAAA é o ano com 4 algarismos
#        MM é o mês com 2 algarismos
#        DD é o dia com 2 algarismos
#
# Mateus S. Teixeira, julho/2020
################################################

# testando se três argumentos são informados
if [ -z $1 ] || [ -z $2 ] || [ -z $3 ]
then
    echo "ERRO! Vc deve fornecer uma data válida no formato AAAA MM DD."
    echo "Forma de uso:"
    echo "      ./paineis.sh 2020 07 28"
    echo ""
    echo "Saindo ..."
    exit
fi

# guardando argumentos em variáveis
ano=$1
mes=$2
dia=$3

# guardando a data inicial da montagem dos paineis
# redirecionando erro para /dev/null para não exibir mensagem de erro do comando date
data_ini=$(date --date "$ano-$mes-$dia" "+%Y-%m-%d" 2>/dev/null)
if [ $? != 0 ]
then
    echo "Erro ao processar data fornecida. Verifique-a, provavelmente inválida."
    echo "Saindo ..."
    exit
else
    echo "A data obtida é $data_ini"
fi

# para cada inicialização do modelo, há 5 dias de previsão, então, 5 paineis!
flag1=0   # flags para sinalizar se algum conjunto de paineis
flag2=0   # não pode ser construído. Enquanto houver algum com 0, segue fazendo
flag3=0   # flag1 -> PNMM; flag2 -> T2m; flag3 -> Espaguete T2m
#flag4=0   # flag4 -> Chuva

for i in {0..4}
do
    data_prev=$(date --date "$data_ini +${i}day" "+%Y-%m-%d" 2>/dev/null)
    echo "Paineis para $data_prev ..."

    # verifica se está tudo ok para paineis para a variável
    if [ $flag1 == 0 ]
    then
	echo -e  "\t para PNMM ..."    # opção '-e' para usar \t
	montage pnmm_media_dp_${data_ini}T00_${data_prev}T* -tile x2 -geometry 1000x800 pnmm_media_dp_${data_ini}T00_${data_prev}_painel.png 2>/dev/null
	if [ $? != 0 ]
	then
	    echo "Erro ao montar painel para PNMM. Verifique disponibilidade dos arquivos!"
	    echo "Abortando paineis para essa variável!"
	    flag1=1
	fi
    fi

    # verifica se está tudo ok para paineis para a variável
    if [ $flag2 == 0 ]
    then
	echo -e  "\t para T2m ..."    # opção '-e' para usar \t
	montage t2m_media_dp_${data_ini}T00_${data_prev}T* -tile x2 -geometry 1000x800 t2m_media_dp_${data_ini}T00_${data_prev}_painel.png 2>/dev/null
	if [ $? != 0 ]
	then
	    echo "Erro ao montar painel para T2m. Verifique disponibilidade dos arquivos!"
	    echo "Abortando paineis para essa variável!"
	    flag2=1
	fi
    fi

    # verifica se está tudo ok para paineis da variável
    if [ $flag3 == 0 ]
    then
	echo -e  "\t para Gráficos Espaguete ..."    # opção '-e' para usar \t
	montage spaghetti_t2m_${data_ini}T00_${data_prev}T* -tile x2 -geometry 1000x800 spaghetti_t2m_${data_ini}T00_${data_prev}_painel.png 2>/dev/null
	if [ $? != 0 ]
	then
	    echo "Erro ao montar painel. Verifique disponibilidade dos arquivos!"
	    echo "Abortando paineis para essa variável!"
	    flag3=1
	fi
    fi

    # verifica se está tudo ok para paineis da variável
#    if [ $flag4 == 0 ]
#    then
#	echo -e  "\t para Chuva ..."    # opção '-e' para usar \t
#	montage chuva_media_dp_${data_ini}T00_${data_prev}T* -tile x2 -geometry 1000x800 chuva_media_dp_${data_ini}T00_${data_prev}_painel.png 2>/dev/null
#	if [ $? != 0 ]
#	then
#	    echo "Erro ao montar painel. Verifique disponibilidade dos arquivos!"
#	    echo "Abortando paineis para essa variável!"
#	    flag4=1
#	fi
#    fi

    
    # se ocorrer erro para todas as variáves, para o script pois provavelmente
    # haverá erros a frente.
    if [ $flag1 != 0 ] && [ $flag2 != 0 ] && [ $flag3 != 0 ] #&& [ $flag4 != 0 ]
    then
	echo "Problemas com a construção dos paineis para todas as variáveis!"
	echo "Verifique disponibilidade dos arquivos!"
	echo -e "Saindo! \n\n\n"
	exit
    fi
    
done

    

