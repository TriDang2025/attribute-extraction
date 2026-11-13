CREATE TABLE "train" (
  "trainid" INTEGER,
  "Train arrive by" TIME,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train duration" INTERVAL,
  "Train leave at" TIME,
  "Train price" NUMERIC(10, 2),
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  PRIMARY KEY ("trainid")
);

CREATE TABLE "hotel" (
  "confirmed reference" INTEGER,
  "Hotel address" TEXT,
  "Hotel area" TEXT,
  "Hotel confirmed reference" INTEGER,
  "Hotel name" TEXT,
  "Hotel phone" INTEGER,
  "Hotel postcode" INTEGER,
  "Hotel price range" TEXT,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  "Hotel stars" INTEGER,
  "Hotel type" TEXT,
  PRIMARY KEY ("confirmed reference")
);

CREATE TABLE "restaurant" (
  "confirmed reference" INTEGER,
  "Restaurant address" TEXT,
  "Restaurant area" TEXT,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant food" TEXT,
  "Restaurant name" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant postcode" TEXT,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("confirmed reference")
);
