# Dijital Kitabe aracı: adım adım kullanım kılavuzu

Bu kılavuz hiç program çalıştırmamış biri için yazıldı. Adımları sırayla izle, hiçbirini atlama.

Araç dört iş yapar:

| Ne yapmak istiyorsun? | Hangi dosyayı kullanacaksın? |
|---|---|
| Onaylı bir modelin kitabesini (amblem + desen + kayıt) üretmek | `2_KITABE_URET.bat` |
| Gelen bir IFC dosyası onaylı modelle aynı mı, kontrol etmek | `3_DOGRULA.bat` |
| Onaylanmış bir revizyon için yeni kitabe (onarım kitabesi) üretmek | `4_REVIZYON.bat` |
| Elindeki amblem/desen görselinden hangi binaya ait olduğunu bulmak | `5_TANI.bat` |

İlk üç sözcüğü bil, yeter:
- **IFC dosyası:** Revit, ArchiCAD gibi programlardan "IFC olarak dışa aktar" ile aldığın model dosyası (`.ifc`).
- **Kayıt dosyası:** Aracın ürettiği `..._record.json` dosyası. Modelin "nüfus cüzdanı" gibidir. **Asla silme.** Doğrulama ve tanıma bununla yapılır.
- **Model kökü:** 64 haneli bir kod (ör. `19de7e05…`). Modelin parmak izidir. Modelde tek bir kapı değişse bu kod da değişir.

---

## BÖLÜM A: Kurulum (yalnızca bir kez yapılır, yaklaşık 10 dakika)

### A1. Python'u kur

1. Tarayıcıda **https://www.python.org/downloads/** adresine git.
2. Sarı **"Download Python 3.12.x"** düğmesine bas (3.12 ya da 3.13 olabilir; 3.14 ve üstünü seçme).
3. İnen dosyayı çift tıkla.
4. **ÇOK ÖNEMLİ:** Açılan ilk pencerenin en altındaki **"Add python.exe to PATH"** kutusunu işaretle. Bunu unutursan hiçbir şey çalışmaz.
5. **"Install Now"** düğmesine bas, bitince **"Close"**.

> Kutuyu işaretlemeyi unuttuysan: aynı kurulum dosyasını tekrar çalıştır, **"Modify"** de, sonraki ekranda **"Add Python to environment variables"** kutusunu işaretle.

### A2. Araç klasörünü yerleştir

1. `DigitalKitabe_arac.zip` dosyasına sağ tıkla, **"Tümünü ayıkla…"** de.
2. Çıkan `digital_kitabe` klasörünü kolay bir yere taşı. Önerim: `C:\kitabe\digital_kitabe`
   (Masaüstü de olur. Sadece klasör yolunda Türkçe karakter ve boşluk olmaması işleri kolaylaştırır.)

Klasörün içinde şunları görmelisin:

```
1_KURULUM.bat   2_KITABE_URET.bat   3_DOGRULA.bat   4_REVIZYON.bat   5_TANI.bat
dkitabe.py  dkcore.py  dkpattern.py  dksheet.py  requirements.txt  KULLANIM.md  ornek\
```

> `.bat` uzantısını göremiyorsan sorun değil; dosyaların adları yeter. Windows bunları "Windows Toplu İş Dosyası" diye gösterir.

### A3. Gerekli kütüphaneleri kur

1. `1_KURULUM.bat` dosyasına **çift tıkla**.
2. Siyah bir pencere açılır, bir sürü yazı akar. Bekle (2–5 dakika, internet gerekir).
3. Sonunda "Kurulum bitti" ve "Devam etmek için bir tuşa basın" yazar. Bir tuşa bas.

> Windows "Windows kişisel bilgisayarınızı korudu" derse: **"Ek bilgi" → "Yine de çalıştır"**. Bu dosyalar sadece aşağıdaki komutları çalıştırır, içlerini Not Defteri ile açıp görebilirsin.

### A4. Deneme (kurulum çalışıyor mu?)

1. `ornek` klasörünü aç. İçinde `demo_metric.ifc` adlı küçük bir model var.
2. Bu dosyayı fareyle tut, **geri klasöre dön ve `2_KITABE_URET.bat` dosyasının üzerine bırak**.
   (Pratik yol: iki Gezgin penceresini yan yana aç.)
3. Pencere "Kısa bir not yazın" diye sorar. `deneme` yaz, Enter'a bas.
4. Birkaç saniye sonra şunu görmelisin:

```
TAMAM / DONE
  Model kökü / model root : 934281cf2606690b5c8e0bdd7533ad768ffd9387c28b80773255eb37d0632671
  Revizyon / revision      : 0
```

5. `ornek` klasöründe yeni bir `demo_metric_kitabe` klasörü oluşur. İçindeki `demo_metric_rev0_kitabe_emblem.png` dosyasını aç: amblemi göreceksin.

Bunu gördüysen kurulum tamam.

> En üstte `No stream support: No module named 'lark'` yazısı çıkabilir. **Önemsiz**, görmezden gel.

---

## BÖLÜM B: Günlük kullanım

### B1. Onaylı modelin kitabesini üretmek (Rev0)

Ne zaman: Proje onaylandığında, onaylanan IFC dosyası için **bir kez**.

1. Onaylı IFC dosyasını (ör. `Bina.ifc`) **`2_KITABE_URET.bat` üzerine sürükle bırak**.
2. Not sorulunca örneğin `Tasarim onayi` yaz, Enter.
3. Bekle. Küçük modeller saniyeler, 200 MB'lık bir model 2–3 dakika sürer. Pencere donmuş gibi görünebilir, kapatma.
4. "TAMAM" yazınca bir tuşa bas.

IFC dosyasının **yanında** `Bina_kitabe` adlı bir klasör oluşur:

| Dosya | Ne yapacaksın? |
|---|---|
| `Bina_rev0_kitabe_emblem.png` | **Proje kitabesi amblemi.** Pafta antetine, ruhsat/teslim belgelerine, sözleşme ekine koy. |
| `Bina_rev0_kitabe.png` / `.svg` | Yalnızca desen. SVG, büyütülünce bozulmayan çizimdir (baskı için). |
| `Bina_rev0_with_kitabe.ifc` | Kimliği içine gömülmüş IFC. Karşı tarafa bunu gönderebilirsin. |
| `Bina_rev0_kitabe_record.json` | **Kayıt dosyası. Sakla, yedekle, silme.** |

**Altın kural:** Tüm kayıt dosyalarını tek bir klasörde topla, ör. `C:\kitabe\kayitlar`. Doğrulama ve tanıma için bu klasör lazım olacak.

### B2. Gelen bir IFC dosyasını doğrulamak

Ne zaman: Yükleniciden, belediyeden ya da bir meslektaştan IFC geldiğinde, "bu onaylı modelin aynısı mı?" sorusu için.

1. Gelen IFC dosyasını **`3_DOGRULA.bat` üzerine sürükle bırak**.
2. Pencere "kayıt dosyasını bu pencerenin içine sürükleyin" der. Onaylı modelin `..._record.json` dosyasını **siyah pencerenin içine** sürükle bırak (dosya yolu kendiliğinden yazılır), Enter'a bas.
3. Sonuç:
   - **DOĞRULANDI:** İçerik onaylı modelle aynı. Dosya başka programda açılıp yeniden kaydedilmiş olsa bile bu sonuç değişmez.
   - **UYUŞMUYOR:** Araç neyin değiştiğini listeler (hangi kat, hangi disiplin, hangi eleman; eklendi/silindi/değişti). Ayrıca `..._verify_comparison.png` dosyası üretir: iki desen yan yana, değişen bölgeler kırmızı.

### B3. Onaylanan bir revizyonun kitabesi (Rev1, Rev2, …)

Ne zaman: Projede bir değişiklik **onaylandığında**. Böylece onarım kitabesi zinciri oluşur.

1. Revize edilmiş yeni IFC dosyasını **`4_REVIZYON.bat` üzerine sürükle bırak**.
2. Bir önceki onayın kayıt dosyasını (ör. `Bina_rev0_kitabe_record.json`) **pencerenin içine** sürükle, Enter.
3. Revizyon notunu yaz (ör. `L3 kapi revizyonu`), Enter.

Yeni klasörde `..._rev1_...` dosyaları oluşur. Yeni amblemin ortasında güncel desen, altında önceki onayların küçük madalyonları görünür. Ayrıca `..._rev0_vs_rev1.png` karşılaştırma görseli de üretilir.

Bir sonraki revizyonda (Rev2) **Rev1'in** kayıt dosyasını vereceksin; hep bir öncekini.

### B4. Görselden binayı bulmak (tanıma)

Ne zaman: Elinde sadece bir amblem ya da desen görseli var (bir paftadan, rapordan, ekran görüntüsünden) ve hangi projeye/revizyona ait olduğunu bilmek istiyorsun.

1. Görseli (PNG ya da JPG) **`5_TANI.bat` üzerine sürükle bırak**.
2. Kayıtlarının toplandığı klasörü (ör. `C:\kitabe\kayitlar`) **pencerenin içine** sürükle, Enter.
3. Sonuç:
   - **EŞLEŞTİ:** Araç proje adı, bina, adres, eleman/kat sayıları, disiplin dağılımı, revizyon geçmişi ve model kökünü yazar.
   - **KISMİ EŞLEŞME:** Büyük olasılıkla aynı binanın başka bir revizyonu; farklı görünen kat ve disiplinler listelenir.
   - **EŞLEŞME YOK:** Kayıtlı hiçbir modele ait değil.

Bilmen gereken iki şey:
- Bina bilgileri **desenin içinde değil**, eşleşen kayıttan okunur. Desen sadece modelin parmak izini taşır. Bu, model içeriğinin görselden sızmaması için bilinçli bir tercih.
- Kâğıt baskının telefonla çekilmiş, eğik fotoğrafı henüz desteklenmiyor. PNG, PDF'ten alınmış ekran görüntüsü ve JPEG çalışır. Kesin karar her zaman B2'deki IFC doğrulamasıdır.

---

## BÖLÜM C: Bir şey ters giderse

| Ne görüyorsun? | Ne yapmalısın? |
|---|---|
| `'python' is not recognized…` / `'python' iç ya da dış komut olarak tanınmıyor` | Python kurulurken "Add to PATH" işaretlenmemiş. A1'deki nottaki gibi "Modify" ile düzelt, sonra bilgisayarı yeniden başlat. |
| Kurulumda `ERROR: Could not find a version that satisfies ifcopenshell` | Python sürümün çok yeni (3.14 vb.). Python 3.12'yi kur. |
| `No module named 'ifcopenshell'` (ya da numpy, scipy…) | `1_KURULUM.bat` çalıştırılmamış ya da yarıda kalmış. Tekrar çalıştır. |
| `No stream support: No module named 'lark'` | Önemsiz uyarı, görmezden gel. |
| Pencere açılıp hemen kapanıyor | Dosyayı `.bat`'a çift tıklamak yerine **üzerine sürükleyip bıraktığından** emin ol (kurulum hariç). |
| `MemoryError` ya da bilgisayar çok yavaşladı | Model büyük ve RAM yetmiyor. Diğer programları kapat; 200 MB'lık model için 8 GB+ RAM gerekir. |
| `FileNotFoundError` | Dosya yolu yanlış. Kayıt dosyasını pencereye yazmak yerine sürükleyerek ver. |
| DOĞRULAMA "UYUŞMUYOR" diyor ama kimse modeli değiştirmedi | Gerçekten bir şey değişmiş olabilir (ör. dışa aktarma ayarı farklı, bir eleman eksik). Listelenen GlobalId'leri Revit/ArchiCAD'de arayarak kontrol et. |

---

## BÖLÜM D: Komutları elle yazmak (isteğe bağlı, ileri düzey)

`.bat` dosyaları aslında aşağıdaki komutları senin yerine yazar. Mac kullanıyorsan ya da kendin yazmak istersen:

1. Komut penceresini aç:
   - **Windows:** `digital_kitabe` klasörünü aç, üstteki adres çubuğuna tıkla, `cmd` yaz, Enter. Pencere doğrudan o klasörde açılır.
   - **Mac:** Klasöre sağ tık → "Klasörde Yeni Terminal". (Mac'te `python` yerine `python3` yaz.)
2. Kurulum (bir kez): `python -m pip install -r requirements.txt`
3. Komutlar:

```
python dkitabe.py stamp    "C:\projeler\Bina.ifc" --note "Tasarim onayi"
python dkitabe.py verify   "C:\gelen\Bina_yeni.ifc" "C:\kitabe\kayitlar\Bina_rev0_kitabe_record.json"
python dkitabe.py stamp    "C:\projeler\Bina_rev1.ifc" --previous "C:\kitabe\kayitlar\Bina_rev0_kitabe_record.json" --note "L3 kapi revizyonu"
python dkitabe.py identify "C:\belgeler\amblem.png" "C:\kitabe\kayitlar"
```

Ek seçenekler: `--out KLASOR` (çıktıları başka klasöre yaz), `--no-embed` (kimlik gömülmüş IFC kopyası üretme; büyük modellerde zaman kazandırır).
Yardım için: `python dkitabe.py --help`

---

## BÖLÜM E: Makale kodu paketi ne olacak?

Zenodo/GitHub paketindeki `paper/` klasörü **senin çalıştırman gereken bir şey değil.** Makaledeki deneyleri (E1–E5) ve şekilleri üreten koddur; dergi "Data availability" bölümünde söz verdiğimiz için yayımlanır, hakem isterse inceler. Günlük kullanım için yalnızca bu araç klasörü (`tool/`) yeter.

## Notlar

- **Desen bir tanıma aracıdır, güvenlik aracı değildir.** Bağlayıcı karar her zaman doğrulamanın verdiği kök karşılaştırmasıdır.
- **Kayıt dosyası** bu sürümde yereldir; ileride imzalı bir deftere ya da blockchain'e yazma adımı eklenebilir.
- **Amblem modelde nerede durur:** Binanın bir parçası değil, projenin sembolüdür. IFC içinde fiziksel olmayan bir IfcAnnotation (DigitalKitabeEmblem) olarak bina orijininde durur.
- **Disiplin kodları:** Ekranda makaledeki kodlar görünür: STR, WAL, FAC, OPN, CIR, FUR, SPC, OTH.
- Araç, makaledeki kuralların aynısını kullanır: DK-C14N-1.1 ve DK-ENC-1.0.
