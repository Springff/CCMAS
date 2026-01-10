library(CellChat)
library(patchwork)
library(Matrix)
options(stringsAsFactors = FALSE)

mtf <- 'cccm'


for(mtf in c('mcpp'))
{
  path <- paste0("D:/Desktop/GLM/新数据/PDAC/T2b5/output/",mtf,"/")
  if (!file.exists(path)) {
    dir.create(path, recursive = TRUE)
  }
  data.input <- readMM(paste0('D:/Desktop/GLM/新数据/PDAC/T2b5/extracted_matrix/original/',mtf,'/matrix.txt'))
  
  gene_name <- read.csv('D:/Desktop/GLM/新数据/PDAC/T2b5/gene_names.txt',header=FALSE)
  

  
  celltype <- read.csv(paste0('D:/Desktop/GLM/新数据/PDAC/T2b5/extracted_matrix/original/',mtf,'/cell_types.txt'), header = FALSE)
  celltype <- as.vector(celltype$V1)
  
  #celltype1 <- read.csv(paste0('D:/Desktop/GLM/新数据/PDAC/下游分析/pattern_analysis_pipeline/AD-disease/spatial.csv'))
  #celltype1 <- celltype1['top_level_cell_type']
  #celltype1 <- as.vector(celltype$top_level_cell_type)
  
  meta <- data.frame(matrix(nrow = length(celltype), ncol = 0))
  meta$labels <- celltype
  
  data.input@Dimnames[1] <- gene_name
  data.input@Dimnames[[2]] <- 1:data.input@Dim[2]
  
  cellchat <- createCellChat(object = data.input, meta = meta, group.by = "labels")
  
  # use CellChatDB.mouse if running on mouse data
  CellChatDB <- CellChatDB.human 
  
  
  #CellChatDB.use <- subsetDB(CellChatDB, search = "Secreted Signaling")
  CellChatDB.use <- CellChatDB
  cellchat@DB <- CellChatDB.use
  
  cellchat <- subsetData(cellchat) # This step is necessary even if using the whole database
  
  cellchat <- identifyOverExpressedGenes(cellchat)
  cellchat <- identifyOverExpressedInteractions(cellchat)
  
  #cellchat <- computeCommunProb(cellchat)
  
  cellchat_truncatedMean <- computeCommunProb(cellchat,type =  "truncatedMean", trim = 0.1)
  
  df.net <- subsetCommunication(cellchat_truncatedMean)
  write.csv(df.net, file = paste0(path,'LRs.csv'), row.names = FALSE)
  cellchat_truncatedMean <- computeCommunProbPathway(cellchat_truncatedMean)
  cellchat_truncatedMean <- aggregateNet(cellchat_truncatedMean)
  
  #可视化
  groupSize <- as.numeric(table(cellchat_truncatedMean@idents))
  par(mfrow = c(1,2), xpd=TRUE)
  netVisual_circle(cellchat_truncatedMean@net$count, vertex.weight = rowSums(cellchat_truncatedMean@net$count), weight.scale = T, label.edge= F, title.name = "Number of interactions")
  netVisual_circle(cellchat_truncatedMean@net$weight, vertex.weight = rowSums(cellchat_truncatedMean@net$weight), weight.scale = T, label.edge= F, title.name = "Interaction weights/strength")
  

  write.csv(df.net,paste0(path,'net.csv'))
  
  write.csv(cellchat_truncatedMean@net$weight,paste0(path,'weight_truncatedMean.csv'))
  write.csv(cellchat_truncatedMean@net$count,paste0(path,'count_truncatedMean.csv'))
}
  
