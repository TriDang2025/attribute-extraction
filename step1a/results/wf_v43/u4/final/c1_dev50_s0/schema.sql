CREATE TABLE "booking" (
  "description" INTEGER,
  "Train confirmed reference" INTEGER,
  "Train trainid" INTEGER,
  "Hotel confirmed reference" INTEGER,
  "Restaurant confirmed reference" INTEGER,
  PRIMARY KEY ("description")
);

CREATE TABLE "location" (
  "id" INTEGER,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Hotel address" TEXT,
  "Hotel area" TEXT,
  "Hotel name" TEXT,
  "Hotel phone" INTEGER,
  "Hotel postcode" INTEGER,
  "Hotel type" TEXT,
  "Restaurant address" TEXT,
  "Restaurant area" TEXT,
  "Restaurant food" TEXT,
  "Restaurant name" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant postcode" INTEGER,
  PRIMARY KEY ("id")
);

CREATE TABLE "price" (
  "id" INTEGER,
  "Train duration" INTERVAL,
  "Train price" NUMERIC(10, 2),
  "Hotel price range" TEXT,
  "Hotel stars" INTEGER,
  "Restaurant price range" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "time" (
  "id" INTEGER,
  "Train arrive by" TIME,
  "Train day" TEXT,
  "Train leave at" TIME,
  "Hotel requested day" TEXT,
  "Hotel requested stay" INTEGER,
  "Restaurant requested day" TEXT,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("id")
);

CREATE TABLE "people" (
  "id" INTEGER,
  "Train requested people" INTEGER,
  "Hotel requested people" INTEGER,
  "Restaurant requested people" INTEGER,
  PRIMARY KEY ("id")
);
