import netCDF4 as nc
import numpy as np
from datetime import datetime as dt   # manipulação de datas
from datetime import timedelta        # operação com datas
import wrf
import xarray as xr
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.colors

# listagem dos arquivos
listaPrev = os.listdir( '../saidas/' )
listaPrev.sort()     # ordenando a lista de arquivos
iniPrev = dt.strptime( listaPrev[-1], '%Y%m%d_%H' )
dataDir = '../saidas/'+listaPrev[-1]
#print( dataDir )
#exit()
listaArqsFcst = os.listdir( dataDir+'/membro01' )
nArqs = len(listaArqsFcst)    # quantidade de arquivos = quantidade de dias
preNomeArqPrev = 'wrfout_d01_'
strIniPrev = str( iniPrev.year ) + '-' +\
    str( iniPrev.month ).zfill(2) + '-' +\
    str( iniPrev.day ).zfill(2) + 'T' +\
    str( iniPrev.hour ).zfill(2)

# valores, cores e mapa de cores para Desvio Padrão (similar ao ensemble do ECMWF)
cores = ['lawngreen','limegreen','forestgreen','green','white','plum','mediumorchid','fuchsia','magenta','orchid']
limites = [ 0, 0.2, 0.4, 0.6, 0.8, 1.2, 1.8, 2.5, 5, 8, 15 ]
mapa_cores =  matplotlib.colors.ListedColormap( cores )
mapa_cores_norma = matplotlib.colors.BoundaryNorm( limites, mapa_cores.N )


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
            t2m = wrf.getvar( arq, 'T2', wrf.ALL_TIMES )
            tempoPrev = wrf.getvar( arq, 'times', wrf.ALL_TIMES )
            arq.close()
        else:
            #print( '\t acessando membro '+str( membro+1 ) )
            arq = nc.Dataset( dirArq+arqPrev )
            d2 = wrf.getvar( arq, 'T2', wrf.ALL_TIMES )
            arq.close()
            
            d3 = xr.concat( [t2m,d2], dim='membro' )
            
            del t2m, d2
            t2m = d3.copy()
            del d3

    # atribuindo coordenadas para os membros
    t2m = t2m.assign_coords( membro=range(1,21) )
    if len( t2m.shape ) < 4:
        nmembros, nlat, nlon = t2m.shape
    else:
        nmembros, nt, nlat, nlon = t2m.shape
    
    # campos médios e de dispersão
    t2m_media = t2m.mean( dim='membro' )
    t2m_dp    = t2m.std( dim='membro' )

    # criando strings de tempo (p/ gráficos)
    strTempoPrev = np.datetime_as_string( tempoPrev, unit='h' )

    # obtendo informações de projeção e coordenadas dos dados
    # devem ser usadas antes de qualquer conversão de unidades ou operação
    # aritmética
    projecaoWRF = wrf.get_cartopy( t2m )
    lats, lons = wrf.latlon_coords( t2m )
        
    # estados do Brasil
    estados = cfeature.NaturalEarthFeature(category='cultural', scale='50m',
                                           facecolor='none', name='admin_1_states_provinces_shp')

    if len( t2m.shape ) < 4:
        nt = 1
    
    # loop sobre os instantes de tempo do arquivo
    for tPrev in range( 0, nt ):
        print( '\t\t Resultados para '+strTempoPrev[ tPrev ] )
            
        # plotando isoterma de 10 graus para membro 01
        #print( 'Plotando isoterma do membro 1 ...' )
        ax = plt.axes( projection=projecaoWRF )
        if nt==1:
            ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m[ 0, :, :]-273.15 ), [5,10,20],
                        colors=['black','blue','red'],
                        transform=ccrs.PlateCarree() )
        else:
            ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m[ 0, tPrev, :, :]-273.15 ), [5,10,20],
                        colors=['black','blue','red'],
                        transform=ccrs.PlateCarree() )

        ax.coastlines( '50m', linewidth=0.8 )
        ax.set_title('T [C] - PCWRF - CPPMet/FAMET/UFPel \n Início: '+strIniPrev+' Validade: '+strTempoPrev[ tPrev ] )
        ax.set_xlim( wrf.cartopy_xlim( t2m ) )
        ax.set_ylim( wrf.cartopy_ylim( t2m ))
        ax.gridlines( color='black', linestyle='dotted')
        ax.add_feature( estados, linewidth=.5, edgecolor='black' )

        for membro in range( 1, nmembros ):
            #print( 'Plotando isoterma do membro '+str(membro+1)+'...' )
            if nt==1:
                ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m[ membro, :, :]-273.15 ), [5,10,20],
                            colors=['black','blue','red'],
                            transform=ccrs.PlateCarree() )
            else:
                ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m[ membro, tPrev, :, :]-273.15 ), [5,10,20],
                            colors=['black','blue','red'],
                            transform=ccrs.PlateCarree() )

        plt.savefig( 'spaghetti_t2m_'+strIniPrev+'_'+strTempoPrev[ tPrev ]+'.png' )

        
        print('\t\t ... média e desvio padrão para '+strTempoPrev[ tPrev ] )
        plt.cla()
        if nt==1:
            campo1 = ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m_media[ :, :]-273.15 ), colors='black',
                                  levels=np.arange(-10,34,4), linewidths=2., transform=ccrs.PlateCarree() )
            plt.clabel( campo1, fmt='%1.0f' )
            
            campo2 = ax.contourf( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m_dp[ :, :] ),
                                  levels=limites, extend='neither', cmap=mapa_cores, norm=mapa_cores_norma,
                                  transform=ccrs.PlateCarree() )
        else:
            campo1 = ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m_media[ tPrev, :, :]-273.15 ), colors='black',
                                 levels=np.arange(-10,34,4), linewidths=2., transform=ccrs.PlateCarree() )
            plt.clabel( campo1, fmt='%1.0f' )

            campo2 = ax.contourf( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( t2m_dp[ tPrev, :, :] ),
                                  levels=limites, extend='neither', cmap=mapa_cores, norm=mapa_cores_norma,
                                  transform=ccrs.PlateCarree() )
            
        plt.colorbar( campo2, ticks=limites, norm=mapa_cores_norma, boundaries=[0]+limites+[15] )
        ax.coastlines( '50m', linewidth=0.8 )
        ax.set_title('Média (contorno) e DP (colorido) - T [C] \n PCWRF/CPPMet/FAMET/UFPel \n Início: '+strIniPrev+' Validade: '+strTempoPrev[ tPrev ] )
        ax.set_xlim( wrf.cartopy_xlim( t2m ) )
        ax.set_ylim( wrf.cartopy_ylim( t2m ))
        ax.gridlines( color='black', linestyle='dotted')
        ax.add_feature( estados, linewidth=.5, edgecolor='black' )
        plt.savefig( 't2m_media_dp_'+strIniPrev+'_'+strTempoPrev[ tPrev ]+'.png' )
        plt.close()
        
