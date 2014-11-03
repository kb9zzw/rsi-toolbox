#Name:  rsi_parameters.py
#Purpose:  Defines regional snowfall parameters for RSI calculation
#Author:  Jon Burroughs (jdburrou)
#Date:  4/29/2012

# Regional parameters as Python dictionary.  Future
# versions may derive this from other batch processing.
parameters = {
    "ce" : {
        "regionName" : "Central",
        "regionId" : "ce",
        "regionCode" : "103",
        "meanArea" : [ 166266, 87938, 14571, 2625 ],
        "meanPop" : [ 27362537, 15697938, 3246706, 893397 ],     
        "thresholds" : [    [0, 3, 0],
                            [3, 6, 1],
                            [6, 12, 2],
                            [12, 18, 3],
                            [18, 100, 4] ]
    },

    "ec" : {
        "regionName" : "East North Central",
        "regionId" : "ec",
        "regionCode" : "102",
        "meanArea" : [ 162134, 79090, 12480, 1937 ],
        "meanPop" : [ 17070832, 8580093, 1332278, 164656 ],
        "thresholds" : [    [0, 3, 0],
                            [3, 7, 1],
                            [7, 14, 2],
                            [14, 21, 3],
                            [21, 100, 4] ]        
    },
        
    "se" : {
        "regionName" : "Southeast",
        "regionId" : "se",
        "regionCode" : "104",
        "meanArea" : [ 92474, 56935, 18382, 6068 ],
        "meanPop" : [ 15386476, 9335741, 2875746, 1038792 ],
        "thresholds" : [    [0, 2, 0],
                            [2, 5, 1],
                            [5, 10,  2],
                            [10, 15, 3],
                            [15, 100, 4] ]
    },
            
    "ne" : {
        "regionName" : "Northeast",
        "regionId" : "ne",
        "regionCode" : "101",
        "meanArea" : [ 134060, 67762, 8144, 1525 ],
        "meanPop" : [ 49976651, 27785225, 2888413, 279261 ],
        "thresholds" : [    [0, 4, 0],
                            [4, 10, 1],
                            [10, 20, 2],
                            [20, 30, 3],
                            [30, 100, 4] ]
    },

    "sp" : {
        "regionName" : "Southern Plains",
        "regionId" : "sp",
        "regionCode" : "106",
        "meanArea" : [ 193105, 77935, 14161, 3269 ],
        "meanPop" : [ 10596758, 3821078, 626550, 131978 ],
        "thresholds" : [    [0, 2, 0],
                            [2, 5, 1],
                            [5, 10, 2],
                            [10, 15, 3],
                            [15, 100, 4] ]
    },

    "wc" : {
        "regionName" : "West North Central",
        "regionId" : "wc",
        "regionCode" : "105",
        "meanArea" : [ 253633, 114015, 22471, 6824 ],
        "meanPop" : [ 2281931, 1096858, 203677, 50384 ],
        "thresholds" : [    [0, 3, 0],
                            [3, 7, 1],
                            [7, 14, 2],
                            [14, 21, 3],
                            [21, 100, 4] ]
    }
}