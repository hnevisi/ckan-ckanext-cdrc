library(rgdal)
library(rgeos)
library(maptools)
setwd("/Users/alex/Dropbox/Projects/CDRC_LAD_Icon/")
LAD <- readOGR(".", "GB")

LAD_LIST <- LAD@data$CODE


l_LAD <- c("W06000018", "W06000008", "S12000035", "E06000009","E07000174","E07000172", "E07000178","E07000147","E07000144", "E07000128","E07000126",
           "E07000121","E07000116","E07000115","E07000096","E07000095","E07000091","E07000080","E07000079","E07000075", "E07000069","E07000063",
           "E07000062","E07000041","E07000033","E07000010","E07000052","E07000043","E07000039","E07000037","E07000035","E07000033",
           "E07000011","E06000020","E06000017","E06000017","E09000028","E09000022","E09000021","E09000020","E09000018","E08000024","E08000037","E08000014","E08000012","E08000003",
           "E07000243","E07000228","E07000227","E07000224","E07000223","E06000046","E06000039","E06000035","E06000033","E06000028","E06000013","E06000011","E06000002",
           "E07000200","E07000191","E07000188","E06000039","E07000167","E07000168","E07000168")
exl_LAD <- c("S12000023","S12000021","S12000020","S12000013", "E07000145","E07000090","E07000053","E07000046","E07000027","E07000053",
             "E07000041","E07000028","E07000010","E07000006","E06000053","E06000010","E06000006","E06000041")


for (i in 1:length(LAD_LIST)) {

bf<- ifelse(LAD_LIST[i] %in% l_LAD,
              sqrt((bbox(LAD[LAD$CODE == LAD_LIST[i],])[2]-bbox(LAD[LAD$CODE == LAD_LIST[i],])[4])^2+(bbox(LAD[LAD$CODE == LAD_LIST[i],])[1]-bbox(LAD[LAD$CODE == LAD_LIST[i],])[3])^2) *.7,
              ifelse(LAD_LIST[i] %in% exl_LAD,sqrt((bbox(LAD[LAD$CODE == LAD_LIST[i],])[2]-bbox(LAD[LAD$CODE == LAD_LIST[i],])[4])^2+(bbox(LAD[LAD$CODE == LAD_LIST[i],])[1]-bbox(LAD[LAD$CODE == LAD_LIST[i],])[3])^2) *.9,
                     sqrt((bbox(LAD[LAD$CODE == LAD_LIST[i],])[2]-bbox(LAD[LAD$CODE == LAD_LIST[i],])[4])^2+(bbox(LAD[LAD$CODE == LAD_LIST[i],])[1]-bbox(LAD[LAD$CODE == LAD_LIST[i],])[3])^2) *.5))
  

png(filename = paste0(LAD_LIST[i],".png"),width = 1000, height = 1000, units = "px", pointsize = 12, bg = "transparent",  res = 150)
plot(gBuffer(SpatialPoints(coordinates(LAD[LAD$CODE == LAD_LIST[i],])),width=bf,byid=TRUE,quadsegs=30),border=NA,col="white")
plot(LAD[LAD$CODE == LAD_LIST[i],],col="black",add=TRUE)
dev.off()
system(paste0("convert ",getwd(),"/",paste(LAD_LIST[i]),".png -trim ", paste0(getwd(),"/",paste(LAD_LIST[i]),".png")) ,wait=TRUE,ignore.stdout = TRUE, ignore.stderr = TRUE)

}

system("sips -Z 200 ./Icons/*.png")
