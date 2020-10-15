'''
Script para extração de séries temporais das previsões da PCWRF nas coordenadas
das estações meteorológicas do INMET no estado do RS.
'''
import netCDF4 as nc
import numpy as np
from datetime import datetime as dt   # manipulação de datas
from datetime import timedelta        # operação com datas
import wrf
import pandas as pd
import xarray as xr
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.colors

'''
 Parâmetros para extração de variáveis (por enquanto, 2D apenas):

 -----------------------------------------------------------------------------------------------------------------------
  Variável a ser obtida        | String a ser colocada       | Observações
                               | na variável 'varMet_nome'   |
 ----------------------------------------------------------------------------------------------------------------------
 PNMM                          :           slp               | PNMM em hPa
 temperatura em 2m             :           T2                | Temperatura em K
 chuva                         :          chuva              | chuva total acumulativa [convectiva(RAINC)+não convectiva(RAINNC)]
 vento (velocidade e direção   :          vento              | velocidade e direção do vento em 10m rotacionados (uvmet10_wspd_wdir)
 umidade relativa em 2m        :           rh2               | umidade relativa em %
 ----------------------------------------------------------------------------------------------------------------------
'''
varMet_nome = 'rh2'   # nome da variável na saída do WRF
conversao = 0           # fator usado para conversão de unidade de medida (em construção)

# Joguei todas as estações numa struct para ser consumida como dados e não como parametros em código
# O interessante seria conseguir a lista de estações do inmet e isso ser consumido apenas informando as cidades na mesma estrutura (posso implementar isso)
estacoes_met=pd.read_json("stationCities.json")  # tabela com coordenada das estações

# listagem dos arquivos
listaPrev = os.listdir( '../saidas/' )               # lista de diretórios
listaPrev.sort()                                     # ordenando a lista de arquivos
iniPrev = dt.strptime( listaPrev[-1], '%Y%m%d_%H' )  # data do último diretório da listagem
dataDir = '../saidas/'+listaPrev[-1]                 # definindo último diretório como fonte de dados
listaArqsFcst = os.listdir( dataDir+'/membro01' )    # lista de arquivos (nomes iguais para todos membros)
nArqs = len(listaArqsFcst)                           # quantidade de arquivos = quantidade de dias
preNomeArqPrev = 'wrfout_d01_'                       # prefixo nomes dos arquivos
strIniPrev = str( iniPrev.year ) + '-' +\
    str( iniPrev.month ).zfill(2) + '-' +\
    str( iniPrev.day ).zfill(2) + 'T' +\
    str( iniPrev.hour ).zfill(2)

# LOOP dos dias de previsão
flag_concat_inmet = 0    # sinaliza se união das séries iniciou ou não: 0 = não iniciou (primeira passagem)
for deltaDia in range(0,nArqs):  # loop sobre os dias de previsão (cada arquivo contém um dia)

    # dia da previsão analisada
    diaPrev = iniPrev + timedelta( days=deltaDia )  # adiciona a var do loop, igual a qtde dias a mais
    strDiaPrev = str( diaPrev.year ) + '-' +\
        str( diaPrev.month ).zfill(2) + '-' +\
        str( diaPrev.day ).zfill(2) + '_' +\
        str( diaPrev.hour ).zfill(2)

    # cada dia de previsão consta em um arquivo
    print('Previsões para o dia '+strDiaPrev )
    
    arqPrev = preNomeArqPrev + strDiaPrev     # composição do nome do arquivo a ser lido

    # varrendo os arquivos e copiando previsões
    #   vai EXISTIR UM LOOP INTERNO COM OS DIAS DIFERENTES
    #       POIS OS ARQUIVOS ESTAO SEPARADOS POR DIA
    #
    print( '\t Acessando arquivos ...')
    for membro in range(0,20):

        # definindo o membro do qual se obterá as previsões
        dirArq = dataDir+'/membro'+str(membro+1).zfill(2)+'/' # zfill preenche esquerda com zeros, 2 dígitos

        ''' if para verificar se é primeiro membro. Em caso positivo, abre arquivo e cria variável que
        receberá todos os dados. Caso contrário, o primeiro membro já foi lido e continua lendo os 
        dados e armazenando na variávei criada quando o primeiro membro foi aberto.
        '''
        if membro == 0:
            arq = nc.Dataset( dirArq+arqPrev )          # abrindo arquivo

            tempoPrev = wrf.getvar( arq, 'times', wrf.ALL_TIMES ) # obtendo tempos do arquivo
            estacoes_met_wrf = wrf.ll_to_xy( arq,                 # coordenadas (X,Y) das estações INMET
                                             estacoes_met.iloc[:,1].tolist(),
                                             estacoes_met.iloc[:,2].tolist() )

            if varMet_nome == 'chuva':      # verificando se variável é de chuva
                chuvac = wrf.getvar( arq, 'RAINC', wrf.ALL_TIMES )
                chuvanc = wrf.getvar( arq, 'RAINNC', wrf.ALL_TIMES )
                varMet = chuvac+chuvanc
                varMet = varMet.rename( 'chuva' )
                flag_chuva = True
                flag_vento = False
            elif varMet_nome == 'vento':
                varMet = wrf.getvar( arq, 'uvmet10_wspd_wdir', wrf.ALL_TIMES )
                flag_vento = True
                flag_chuva = False
            else:
                varMet = wrf.getvar( arq, varMet_nome, wrf.ALL_TIMES )
                flag_vento = False
                flag_chuva = False
            
            arq.close()   # fechando arquivo
            
        else:
            
            arq = nc.Dataset( dirArq+arqPrev )   # abrindo arquivo

            if flag_chuva:  # verificando se continuação é para chuva 
                chuvac = wrf.getvar( arq, 'RAINC', wrf.ALL_TIMES )
                chuvanc = wrf.getvar( arq, 'RAINNC', wrf.ALL_TIMES )
                d2 = chuvac+chuvanc
                del chuvac, chuvanc
            elif flag_vento:
                d2 = wrf.getvar( arq, 'uvmet10_wspd_wdir', wrf.ALL_TIMES )
            else:
                d2 = wrf.getvar( arq, varMet_nome, wrf.ALL_TIMES )

            arq.close()

            # unindo parte anterior dos dados com a atual
            d3 = xr.concat( [ varMet, d2 ], dim='membro' )

            # apagando variáveis que serão renovadas
            # e guardando união na variável de interesse
            del varMet, d2
            varMet = d3.copy()
            del d3


    # atribuindo coordenadas para os membros
    varMet = varMet.assign_coords( { 'membro': range(1,21) } )
    
    #print( varMet )
    #print( varMet.dims )
    #print( varMet.shape )
    #exit()     # CONTINUAR ALTERAÇÃO: vento possui mais dimensões.
    
    # obtendo dados para as estações e salvando em um arquivo CSV
    if not flag_vento and len( varMet.shape ) < 4:
        varMet_estacoes_met = varMet[ :, estacoes_met_wrf[1,:], estacoes_met_wrf[0,:] ] 
        # Adiciona-se uma coordenada 'Time' para que se possa juntar as informações, pois
        # quando o arquivo contém apenas um instante de tempo, essa coordenada não é incluída
        # isso é importante para unir as séries de todos os membros
        varMet_estacoes_met = varMet_estacoes_met.assign_coords( { 'Time': diaPrev } )
    elif flag_vento and len( varMet.shape ) < 5:
        varMet_estacoes_met = varMet[ :, :, estacoes_met_wrf[1,:], estacoes_met_wrf[0,:] ]
        varMet_estacoes_met = varMet_estacoes_met.assign_coords( { 'Time': diaPrev } )
    else:
        if flag_vento:
            varMet_estacoes_met = varMet[ :, :, :, estacoes_met_wrf[1,:], estacoes_met_wrf[0,:] ]
        else:
            varMet_estacoes_met = varMet[ :, :, estacoes_met_wrf[1,:], estacoes_met_wrf[0,:] ]

    ''' 
    Aqui se usa a mesma estratégia da união dos dados em ponto de grade do modelo,
    mas para os dados nos pontos das estações meteorológicas. Usa-se 'flag_concat_inmet' para 
    detectar a primeira passagem do 'for'
    '''
    if flag_concat_inmet == 0:
        varMet_final = varMet_estacoes_met.copy()
        flag = 1
    else:
        varMet_dummy = xr.concat( [ varMet_final, varMet_estacoes_met ], dim='Time' )
        del varMet_final
        varMet_final = varMet_dummy.copy()
        del varMet_dummy, varMet_estacoes_met
        

# gravando todos os dados no arquivo CSV
varMet_final.to_dataframe().to_csv( varMet_nome+'_estacoes_inmet_pcwrf_'+strIniPrev+'.csv' )
