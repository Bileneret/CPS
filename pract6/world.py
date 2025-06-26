
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from cartopy.feature import ShapelyFeature

OUTPUT_FILENAME = 'russia.png'

def generate_russia_map(filename, width=1920, height=1080, dpi=100):
    # 1) Підготовка фігури та проекції
    fig = plt.figure(figsize=(width/dpi, height/dpi), dpi=dpi)
    ax = fig.add_subplot(1,1,1, projection=ccrs.PlateCarree())

    # 2) Завантажуємо полігoн Росії з Natural Earth
    shp_path = shpreader.natural_earth(resolution='110m',
                                       category='cultural',
                                       name='admin_0_countries')
    reader = shpreader.Reader(shp_path)
    russia_records = [r for r in reader.records() if r.attributes['ADMIN'] == 'Russia']
    if not russia_records:
        raise RuntimeError("Не вдалося знайти полігон Росії у shapefile")
    russia_geom = russia_records[0].geometry

    # 3) Обрізаємо відображення лише під bounding box Росії
    minx, miny, maxx, maxy = russia_geom.bounds
    margin = 1.0  # градус відступу
    ax.set_extent([minx - margin, maxx + margin,
                   miny - margin, maxy + margin],
                  crs=ccrs.PlateCarree())

    # 4) Малюємо фон (вода)
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    # 5) Малюємо контур та заливку самої Росії
    russia_feature = ShapelyFeature(
        [russia_geom],
        crs=ccrs.PlateCarree(),
        facecolor='lightgray',
        edgecolor='black',
        linewidth=0.8
    )
    ax.add_feature(russia_feature)

    # 6) Оформлення та збереження
    plt.tight_layout(pad=0)
    fig.savefig(filename, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    print(f"Карту збережено в «{filename}»")

if __name__ == '__main__':
    generate_russia_map(OUTPUT_FILENAME)
