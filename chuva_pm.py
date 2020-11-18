import netCDF4 as nc
import numpy as np
from datetime import datetime as dt   # manipulação de datas
from datetime import timedelta        # operação com datas
import wrf                            # funções para dados do WRF
import xarray as xr
import os
import cartopy.crs as ccrs            # mapas em projeções
import cartopy.feature as cfeature    # para inclusão das divisões políticas
import matplotlib.pyplot as plt
import matplotlib.colors              # para criação dos mapas de cores


# listagem dos arquivos
listaPrev = os.listdir( '../saidas/' )
listaPrev.sort()     # ordenando a lista de arquivos
iniPrev = dt.strptime( listaPrev[-1], '%Y%m%d_%H' )
dataDir = '../saidas/'+listaPrev[-1]
listaArqsFcst = os.listdir( dataDir+'/membro01' )
nArqs = len(listaArqsFcst)    # quantidade de arquivos = quantidade de dias
preNomeArqPrev = 'wrfout_d01_'
strIniPrev = str( iniPrev.year ) + '-' +\
    str( iniPrev.month ).zfill(2) + '-' +\
    str( iniPrev.day ).zfill(2) + 'T' +\
    str( iniPrev.hour ).zfill(2)


# cores e mapa de cores para Desvio Padrão (similar ao ensemble do ECMWF)
# CORES PARA CAMPOS DE CHUVA
cores_chuva = [ 'white',
                'lime', 'limegreen', 'mediumseagreen', 'green',
                'cyan', 'skyblue', 'cornflowerblue', 'steelblue', 'dodgerblue',
                'burlywood', 'peru', 'chocolate', 'red',
                'crimson', 'black' ]   # similar ao campo de chuva do GFS
limites_chuva = [ 0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 25 ]
mapa_cores_chuva = matplotlib.colors.ListedColormap( cores_chuva )
mapa_cores_chuva_norma = matplotlib.colors.BoundaryNorm( limites_chuva, mapa_cores_chuva.N )


# LOOP dos dias de previsão
for deltaDia in range(0,nArqs):

    # dia da previsão analisada
    diaPrev = iniPrev + timedelta( days=deltaDia )
    strDiaPrev = str( diaPrev.year ) + '-' +\
        str( diaPrev.month ).zfill(2) + '-' +\
        str( diaPrev.day ).zfill(2) + '_' +\
        str( diaPrev.hour ).zfill(2)
    
    # cada dia de previsão consta em um arquivo
    print('Previsões para o dia '+strDiaPrev )
    
    # definindo o nome do arquivo a ser lido de cada membro
    arqPrev = preNomeArqPrev + strDiaPrev

    # varrendo os arquivos e copiando previsões
    #   vai EXISTIR UM LOOP INTERNO COM OS DIAS DIFERENTES
    #       POIS OS ARQUIVOS ESTAO SEPARADOS POR DIA
    #
    print( '\t Acessando arquivos ...')
    for membro in range(0,20):
    
        # definindo o membro do qual se obterá as previsões
        dirArq = dataDir+'/membro'+str(membro+1).zfill(2)+'/' # zfill preenche esquerda com zeros, 2 dígitos
        
        if membro == 0:
            #print( '\t acessando membro 1' )
            arq = nc.Dataset( dirArq+arqPrev )

            chuvac = wrf.getvar( arq, 'RAINC', wrf.ALL_TIMES )
            chuvanc = wrf.getvar( arq, 'RAINNC', wrf.ALL_TIMES )
            varMet = chuvac+chuvanc
            varMet = varMet.rename( 'chuva' )

            if deltaDia == 0:
                projecaoWRF = wrf.get_cartopy( wrfin=arq )    # projeção dos dados -> para plotagem
                dominioLimsX = wrf.cartopy_xlim( wrfin=arq )
                dominioLimsY = wrf.cartopy_ylim( wrfin=arq )

            arq.close()

        else:

            #print( '\t acessando membro '+str( membro+1 ) )
            arq = nc.Dataset( dirArq+arqPrev )

            chuvac = wrf.getvar( arq, 'RAINC', wrf.ALL_TIMES )
            chuvanc = wrf.getvar( arq, 'RAINNC', wrf.ALL_TIMES )
            d2 = chuvac+chuvanc
            del chuvac, chuvanc

            arq.close()
            
            d3 = xr.concat( [ varMet, d2 ], dim='membro' )

            # apagando variáveis que serão renovadas
            # e guardando união na variável de interesse
            del varMet, d2
            varMet = d3.copy()
            del d3


    # atribuindo coordenadas para os membros
    varMet = varMet.assign_coords( membro=range(1,21) )

    # salvando arranjo para o próximo dia
    if deltaDia ==0:
        varMet_rodada = varMet
        del varMet
    else:
        d3 = xr.concat( [ varMet_rodada, varMet ], dim='Time' )
        del varMet_rodada, varMet
        varMet_rodada = d3.copy()
        del d3


# calculando a chuva acumulada em 3h
# a diferença de tempo entre cada instante de tempo é de 3h
# então diff é usado
varMet_rodada = varMet_rodada.diff( 'Time' )
nmembros, nt, nlat, nlon =  varMet_rodada.shape

# acumulados maiores podem ser feitos a partir do
# acúmulo de 3h
#chuva_24h = varMet_rodada.resample(Time='24H').sum()
#chuva_24h_media = chuva_24h.mean( dim='membro' )
#chuva_24h_dp    = chuva_24h.std( dim='membro' )

# campos médios
varMet_media = varMet_rodada.mean( dim='membro' )

#### SEÇÃO DO PROBABILITY MATCHED ENSEMBLE MEAN
# obtendo o ranqueamento dos pontos de grade
rank_media = varMet_media
for t in range(0, nt):
    rank_media_ts = varMet_media[t,:,:].to_series().rank( ascending=False, method='first')
    rank_media[t,:,:] = xr.DataArray.from_series( rank_media_ts )

print( rank_media[0,:,:] )
exit()



# criando strings de tempo (p/ gráficos)
strTempoPrev = np.datetime_as_string( varMet_rodada.Time, unit='h' )

# obtendo informações de coordenadas dos dados
# devem ser usadas antes de qualquer conversão de unidades ou operação
# aritmética
lats, lons = wrf.latlon_coords( varMet_rodada )
        
# estados do Brasil
estados = cfeature.NaturalEarthFeature( category='cultural', scale='50m',
                                        facecolor='none', name='admin_1_states_provinces_shp')
paises  = cfeature.NaturalEarthFeature( category='cultural', scale='50m',
                                        facecolor='none', name='admin_0_countries' )

'''
CONSTRUIR PAINEL COM DOIS GRÁFICOS: UM PARA MÉDIA E OUTRO PARA DP (O MESMO PARA OS DEMAIS CAMPOS, DEPOIS!)
'''
# loop sobre os instantes de tempo do arquivo
for tPrev in range( 0, nt ):
    print( '\t\t Resultados para '+strTempoPrev[ tPrev ] )

    fig =  plt.figure( figsize=(15,5), dpi=200 )
    fig.suptitle( 'Previsão por Conjunto WRF (20 membros) - CPPMet/FAMET/UFPel \n Chuva acumulada em 3h [mm] - Início: '+strIniPrev+' Validade: '+strTempoPrev[ tPrev ] )
    ax_media = fig.add_subplot( 1, 2, 1, projection=projecaoWRF )
    ax_dp    = fig.add_subplot( 1, 2, 2, projection=projecaoWRF )

    campo1 = ax_media.contourf( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( varMet_media[ tPrev, :, :] ),
                                levels=limites_chuva, extend='max', cmap=mapa_cores_chuva,
                                norm=mapa_cores_chuva_norma, transform=ccrs.PlateCarree() )
    cb_campo1 = fig.colorbar( campo1, ax=ax_media, shrink=0.7 )
    ax_media.set_title('Média' )
    ax_media.coastlines( '50m', linewidth=0.8 )
    ax_media.set_xlim( dominioLimsX )
    ax_media.set_ylim( dominioLimsY )
    ax_media.gridlines( color='black', linestyle='dotted')
    ax_media.add_feature( estados, linewidth=0.5, edgecolor='black' )
    ax_media.add_feature( paises, linewidth=0.5, edgecolor='black' )
                
    campo2 = ax_dp.contourf( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( varMet_dp[ tPrev, :, :] ),
                             levels=limites, extend='max', cmap=mapa_cores, norm=mapa_cores_norma,
                             transform=ccrs.PlateCarree() )
    cb_campo2 = fig.colorbar( campo2, ax=ax_dp, shrink=0.7 )
    ax_dp.set_title('Desvio Padrão' )
    ax_dp.coastlines( '50m', linewidth=0.8 )
    ax_dp.set_xlim( dominioLimsX )
    ax_dp.set_ylim( dominioLimsY )
    ax_dp.gridlines( color='black', linestyle='dotted')
    ax_dp.add_feature( estados, linewidth=.5, edgecolor='black' )
    ax_dp.add_feature( paises, linewidth=0.5, edgecolor='black' )
    
    plt.savefig( 'chuva_3h_media_pm_'+strIniPrev+'_'+strTempoPrev[ tPrev ]+'.png' )
    plt.close()

