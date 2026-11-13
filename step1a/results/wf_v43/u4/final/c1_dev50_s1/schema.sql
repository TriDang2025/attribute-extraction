CREATE TABLE "train" (
  "trainid" INTEGER,
  "Train leave at" TIME,
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  "Train price" NUMERIC(10, 2),
  "Train duration" INTERVAL,
  "Train departure" TEXT,
  "Train arrive by" TIME,
  "Train destination" TEXT,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  PRIMARY KEY ("trainid")
);

CREATE TABLE "hotel" (
  "hotel confirmed reference key" INTEGER,
  "Hotel postcode" INTEGER,
  "Hotel requested people" INTEGER,
  "Hotel type" TEXT,
  "Hotel stars" INTEGER,
  "Hotel name" TEXT,
  "Hotel requested day" TEXT,
  "Hotel price range" TEXT,
  "Hotel address" TEXT,
  "Hotel phone" INTEGER,
  "Hotel area" TEXT,
  "Hotel confirmed reference" INTEGER,
  "Hotel requested stay" INTEGER,
  PRIMARY KEY ("hotel confirmed reference key")
);

CREATE TABLE "restaurant" (
  "confirmed reference" INTEGER,
  "Restaurant food" TEXT,
  "Restaurant postcode" INTEGER,
  "Restaurant phone" INTEGER,
  "Restaurant area" TEXT,
  "Restaurant requested time" TIME,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant address" TEXT,
  "Restaurant name" TEXT,
  PRIMARY KEY ("confirmed reference")
);
