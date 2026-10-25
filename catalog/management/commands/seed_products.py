from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Product,CropProgramme
PRODUCTS=[
("FitoMaster","ROOTS FIRST","Root Establishment","NPK 8:35:4 + MgO + Trace Elements + Humus","ESTABLISH",["Root establishment","Early crop development","Nutrient acquisition","Transplant establishment"]),
("Vivo + TE","BUILD THE CANOPY","Vegetative Performance","NPK 35:8:6 + MgO + Trace Elements","VEGETATIVE",["Vigorous vegetative growth","Canopy building","Active leaf production","Uniform development"]),
("NitroMaster","POWER THE CROP","High-Nitrogen Canopy Nutrition","High-nitrogen + supporting macro/micronutrients","VEGETATIVE",["Vegetative growth","Canopy development","Nutritional momentum"]),
("Dr. Earth (Macromix)","FEED THE SYSTEM","Balanced Crop Nutrition","NPK 24:24:18 + 3% MgO + Trace Elements","BALANCED_NUTRITION",["Balanced NPK nutrition","Vegetative development","Root support","Flowering/reproductive support"]),
("BioNurse Power","NURSE THE CROP","Seaweed Crop Performance","N≥50 g/L, P2O5≥180 g/L, K2O≥170 g/L, OM≥20 g/L","BALANCED_NUTRITION",["Natural seaweed input","Crop performance support","Nutritional programme support"]),
("FruitSet PRO","SET THE FRUIT","Flowering & Fruit Set Support","Specialized reproductive-stage nutrition","FLOWERING_SET",["Flowering","Fruit set","Early fruit development","Crop uniformity"]),
("ZIBOMA","REGULATE THE GROWTH","Growth Regulation & Physiological Balance","Zinc + Boron + Magnesium","GROWTH_REGULATION",["Crop development","Photosynthetic processes","Flowering support","Reproductive development"]),
("CAL-MASTER+TE","BUILD STRONGER FRUIT","Plant Strength & Fruit Development","N 14%, Ca 21%, Mg 3% + B, Cu, Fe, Mn, Mo","FRUIT_STRENGTH",["Calcium nutrition","Magnesium support","Structural development","Quality production"]),
("SeaMax Power","MAKE THE SYSTEM WORK","Nutrient Utilisation & Stress Management","Seaweed-based crop-support solution","STRESS_SUPPORT",["Crop vigour","Stress-period support","Reproductive-stage support"]),
("Inciter Micro","SMALL ELEMENTS, BIG IMPACT","Micronutrient Correction","Zn 3%, Fe 2.5%, B 0.5%, Cu 0.5%, Mn 1%, Mo 0.1%","MICRONUTRIENTS",["Micronutrient correction","Balanced crop development","Enzyme and chlorophyll support"]),
("K25 AgroGreen","BULK THE FRUIT","Fruit Sizing & Bulking","High-potassium + N, P, Mg + Trace Elements","BULKING_FINISH",["Fruit sizing","Bulking","Quality finishing","Potassium nutrition"])]
PRODUCT_IMAGES={
 "FitoMaster":"IMG-20261024-WA0013.jpg",
 "Dr. Earth (Macromix)":"IMG-20261024-WA0007.jpg",
 "FruitSet PRO":"IMG-20261024-WA0002.jpg",
 "ZIBOMA":"IMG-20261024-WA0012.jpg",
 "CAL-MASTER+TE":"IMG-20261024-WA0014.jpg",
 "SeaMax Power":"IMG-20261024-WA0010.jpg",
 "K25 AgroGreen":"IMG-20261024-WA0009.jpg",
 "BioNurse Power":"IMG-20261024-WA0015.jpg",
 "Inciter Micro":"IMG-20261024-WA0003.jpg",
 "NitroMaster":"IMG-20261024-WA0035.jpg",
}
CROPS=["Tomato","Avocado","French Beans","Potatoes","Onions","Roses","Cereals"]
class Command(BaseCommand):
 help="Seed the 11 AgroVivo products and seven crop programme outlines."
 def add_arguments(self,parser):
  parser.add_argument("--force",action="store_true",help="Update existing catalog records from the seed data.")
 def handle(self,*args,**options):
  save_product=Product.objects.update_or_create if options["force"] else Product.objects.get_or_create
  for i,(name,focus,role,form,stage,benefits) in enumerate(PRODUCTS):
   photo=PRODUCT_IMAGES.get(name)
   save_product(slug=slugify(name),defaults={"name":name,"farmer_focus":focus,"primary_role":role,"purpose":f"{role} as part of a stage-based crop nutrition programme.","formulation":form,"stage":stage,"key_benefits":benefits,"best_for":["Crop establishment","Active growth","Production"],"crops":CROPS,"images":[f"/static/images/product-photos/{photo}"] if photo else [],"price_kes":[1200,1650,1450,2200,1850,1800,1350,2400,2100,1100,1900][i],"stock":50,"featured":i in (0,3,5,7),"active":True})
  for crop in CROPS:
   stages=[{"stage":stage,"products":[p[0] for p in PRODUCTS if p[4]==stage],"objective":f"Support {stage.lower().replace('_',' ')} for {crop}."} for stage in dict.fromkeys(p[4] for p in PRODUCTS)]
   save_programme=CropProgramme.objects.update_or_create if options["force"] else CropProgramme.objects.get_or_create
   save_programme(slug=slugify(crop),defaults={"crop_name":crop,"stages":stages})
  action="Updated or created" if options["force"] else "Ensured"
  self.stdout.write(self.style.SUCCESS(f"{action} 11 products and 7 crop programmes. Prices are placeholders; confirm before launch."))
