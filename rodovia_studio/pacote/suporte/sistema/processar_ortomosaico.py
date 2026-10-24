"""CLI do Rodovia Studio para limpeza segura de colar branco externo."""
import argparse,json,sys
from pathlib import Path
from app.orthomosaic import process_orthomosaic,gdal_nearblack_command

def main(argv=None):
    p=argparse.ArgumentParser(description='Remove somente o colar branco externo de ortofotos/ortomosaicos e gera GeoTIFF/COG RGBA.')
    p.add_argument('entrada');p.add_argument('saida')
    p.add_argument('--limiar-branco',type=int,default=248,help='RGB mínimo candidato a branco (padrão 248).')
    p.add_argument('--overview',type=int,default=4096,help='Maior dimensão da visão reduzida usada para detectar a pegada.')
    p.add_argument('--sem-cog',action='store_true');p.add_argument('--guardar-cutline',action='store_true')
    p.add_argument('--mostrar-nearblack',action='store_true',help='Mostra o comando GDAL nearblack conservador e sai.')
    a=p.parse_args(argv)
    if a.mostrar_nearblack:
        print(' '.join(map(str,gdal_nearblack_command(a.entrada,a.saida,threshold=max(0,255-a.limiar_branco)))))
        return 0
    r=process_orthomosaic(a.entrada,a.saida,white_threshold=a.limiar_branco,max_overview=a.overview,
                          cog=not a.sem_cog,keep_cutline=a.guardar_cutline,
                          status=lambda f,t:print(f'{f*100:5.1f}% {t}'))
    print(json.dumps(r,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':sys.exit(main())
