from app.models import db, SchoolClass, Subject, SyllabusChapter, SyllabusTopic, AcademicSession, Institute

CBSE_CURRICULUM_DATA = {
    "1": {
        "Mathematics": [
            ("Shapes and Space", ["Top and Bottom, Inside and Outside", "3D Shapes & Spatial Understanding"]),
            ("Numbers 1 to 9", ["Counting 1 to 9", "More or Less Comparison", "Zero Concept"]),
            ("Addition up to 9", ["One-Digit Addition", "Addition Word Problems"]),
            ("Subtraction up to 9", ["Taking Away Concept", "Subtraction Exercises"]),
            ("Numbers 10 to 20", ["Tens and Ones Intro", "Counting 10 to 20"]),
            ("Time & Daily Routine", ["Morning, Afternoon, Evening", "Daily Sequence"]),
            ("Measurement", ["Handspans and Heights", "Longer and Shorter"]),
            ("Numbers 21 to 100", ["Counting to 50", "Counting to 100"]),
            ("Patterns & Sequences", ["Shape Patterns", "Number Sequences"]),
            ("Money", ["Coins and Notes Recognition", "Simple Money Value Addition"])
        ],
        "English": [
            ("Unit 1: Phonics & Rhymes", ["Two Little Hands & Body Rhymes", "Alphabet Phonics"]),
            ("Unit 2: Stories & Words", ["The Cap-seller & Monkeys", "Sight Words"]),
            ("Unit 3: Animal World", ["Farm Animals & Sounds", "CVC 3-Letter Blends"])
        ],
        "Hindi": [
            ("इकाई १: परिवार और झूले", ["मीना का परिवार", "दादा-दादी और झूला"]),
            ("इकाई २: प्रकृति और जानवर", ["रीना का दिन & आम की टोकरी", "पशु-पक्षियों की बोलियाँ"]),
            ("इकाई ३: गिनती", ["हिंदी गिनती (१ से २०)"])
        ],
        "EVS": [
            ("My Self & Body", ["My Body & Sense Organs", "Personal Hygiene"]),
            ("Family & Home", ["Family Relationships", "Types of Shelter"]),
            ("Food & Health", ["Healthy Food & Clean Water", "Safety Rules"])
        ],
        "Computer": [
            ("Computer Basics", ["Intro to Smart Machines", "Main Parts (Monitor, CPU, Mouse, Keyboard)"]),
            ("Lab Culture", ["Uses of Computer in School & Home", "Lab Etiquette"])
        ]
    },
    "2": {
        "Mathematics": [
            ("What is Long, What is Round?", ["Rolling and Sliding Objects", "Sorting 3D Shapes"]),
            ("Counting in Groups", ["Pairs and Groups Counting", "Estimation"]),
            ("How Much Can You Carry?", ["Weight Balance", "Heavier and Lighter"]),
            ("Counting in Tens", ["2-Digit Tens & Ones", "Expanded Forms"]),
            ("Jugs and Mugs", ["Capacity Measurement", "Liquid Jugs & Mugs"]),
            ("Days and Months", ["Calendar Navigation", "Seasons & Months"]),
            ("Give and Take", ["Mental Addition & Subtraction", "2-Digit Word Problems"]),
            ("Lines and Patterns", ["Straight & Curved Lines", "Repeating Patterns"])
        ],
        "English": [
            ("Unit 1: School & Feelings", ["First Day at School", "I am Lucky!"]),
            ("Unit 2: Nature & Magic", ["The Wind and the Sun", "Storm in the Garden"]),
            ("Unit 3: Fun & Manners", ["Zoo Manners", "Magic Porridge Pot"])
        ],
        "Hindi": [
            ("इकाई १: कहानियाँ", ["ऊँट चला", "भालू ने खेली फुटबॉल"]),
            ("इकाई २: समझदारी", ["अधिक बलवान कौन?", "दोस्त की मदद"]),
            ("इकाई ३: कल्पना", ["मेरी किताब और तितली", "नटखट चूहा"])
        ],
        "EVS": [
            ("Human Body", ["Sense Organs & Functions", "Good Habits"]),
            ("Our Helpers", ["Community Helpers & Professions", "Types of Houses"]),
            ("Environment", ["Water Conservation", "Means of Transport"])
        ],
        "Computer": [
            ("Computer Operations", ["IPO Cycle (Input-Process-Output)", "Starting & Shutting Down Safely"]),
            ("Creative Paint", ["Tux Paint Tools", "Drawing Canvas Shapes"])
        ]
    },
    "3": {
        "Mathematics": [
            ("Where to Look From", ["Top, Front, Side Views", "Mirror Halves Symmetry"]),
            ("Fun with Numbers", ["3-Digit Numbers Reading & Writing", "Place Value & Expanded Form"]),
            ("Give and Take", ["Addition/Subtraction with Regrouping", "Word Problems"]),
            ("Long and Short", ["Length Measurement (cm, m)", "Distance Estimation"]),
            ("Shapes and Designs", ["Tangrams and Tessellations", "Edges and Corners"]),
            ("Fun with Give and Take", ["Subtractions & Checking Answers", "Mental Math Shortcuts"]),
            ("Time Goes On", ["Clocks, Hours, Minutes", "Age Calculations & Calendars"]),
            ("Who is Heavier?", ["Weight Measurement (kg, g)", "Balancing Scale Exercises"]),
            ("Can We Share?", ["Equal Sharing (Division)", "Multiplication & Division Relation"]),
            ("Rupees and Paise", ["Money Addition & Subtraction", "Making Bills & Receipts"])
        ],
        "English": [
            ("Unit 1: Morning & Magic", ["Good Morning Rhyme", "The Magic Garden"]),
            ("Unit 2: Bird Life", ["Nina and the Baby Sparrows", "Little by Little"]),
            ("Unit 3: Ocean & Sea", ["Sea Song", "A Little Fish Story"])
        ],
        "Hindi": [
            ("इकाई १: शैतानी और समझ", ["शेखीबाज़ मक्खी", "चाँद वाली अम्मा"]),
            ("इकाई २: बहादुरी", ["बहादुर बित्तो", "टिपटिपवा"]),
            ("इकाई ३: समाज", ["बंदर बाँट", "सबसे अच्छा पेड़"])
        ],
        "EVS": [
            ("Living World", ["Poonam's Day Out", "Plant Fairy & Leaves"]),
            ("Water & Shelter", ["Water O' Water", "Chhotu's House & Food Diversity"]),
            ("Animals & Nature", ["Sign Language & Flying High Birds", "Cooking Fuels & Vehicles"])
        ],
        "Computer": [
            ("Hardware & Software", ["Hardware vs Software Definitions", "Windows Desktop Navigation"]),
            ("MS Paint & WordPad", ["MS Paint Advanced Tools", "WordPad Typing & Formatting"])
        ]
    },
    "4": {
        "Mathematics": [
            ("Building with Bricks", ["Brick Patterns and Arches", "3D Net Diagrams"]),
            ("Long and Short", ["Kilometres and Metres", "Scale Measurements"]),
            ("A Trip to Bhopal", ["Distance & Speed Estimation", "Bus Trip Word Problems"]),
            ("Tick-Tick-Tick", ["24-Hour Clock vs 12-Hour Clock", "Timelines & Expiry Dates"]),
            ("The Way The World Looks", ["Top and Perspective Views", "Map Reading & Coordinates"]),
            ("The Junk Seller", ["Profit & Loss Introduction", "Currency Multiplication"]),
            ("Jugs and Mugs", ["Capacity (Litres & Millilitres)", "Volume Addition"]),
            ("Carts and Wheels", ["Circle Radius and Diameter", "Drawing Circles with Compass"]),
            ("Halves and Quarters", ["Fractions Introduction (1/2, 1/4, 3/4)", "Shading & Equivalence"]),
            ("Play with Patterns", ["Number Patterns & Decoding Messages", "Rotational Symmetry"]),
            ("Tables and Shares", ["Long Division Methods", "Word Problems on Equal Distribution"]),
            ("Fields and Fences", ["Perimeter of Shapes", "Grid Area Calculations"])
        ],
        "English": [
            ("Unit 1: Morning Routine", ["Neha's Alarm Clock", "The Little Fir Tree"]),
            ("Unit 2: Aim & Wonder", ["Nasruddin's Aim", "Alice in Wonderland"]),
            ("Unit 3: Courage & Language", ["Helen Keller", "The Scholar's Mother Tongue"])
        ],
        "Hindi": [
            ("इकाई १: कल्पना व खेल", ["मन के भोले-भाले बादल", "किरमिच की गेंद"]),
            ("इकाई २: पोशाक व दान", ["दोस्त की पोशाक", "दान का हिसाब"]),
            ("इकाई ३: स्वतंत्रता", ["स्वतंत्रता की ओर (गांधीजी)", "थप्प रोटी थप्प दाल"])
        ],
        "EVS": [
            ("Transport & Animals", ["Going to School (Bridges/Vallams)", "Ear to Ear & Elephant Herds"]),
            ("Trees & Nature", ["Amrita's Trees", "Anita and the Honeybees"]),
            ("Journeys & Rivers", ["Omana's Train Journey", "River Pollution & Water Cycle"])
        ],
        "Computer": [
            ("Computer Memory", ["RAM vs ROM & Storage (SSD/Cloud)", "File Explorer Management"]),
            ("Word & Scratch", ["MS Word Text Formatting & Alignment", "Scratch Block Programming Intro"])
        ]
    },
    "5": {
        "Mathematics": [
            ("The Fish Tale", ["Indian & International Place Value (Lakhs/Crores)", "Speed, Distance & Time"]),
            ("Shapes and Angles", ["Right, Acute & Obtuse Angles", "Degree Clock & Protractors"]),
            ("How Many Squares?", ["Grid Area Calculations", "Perimeter of Irregular Polygons"]),
            ("Parts and Wholes", ["Fractional Operations", "Equivalent Fractions & Simplification"]),
            ("Does it Look the Same?", ["1/2, 1/4, 1/6 Turns", "Rotational Symmetry & Mirror Lines"]),
            ("Be My Multiple, I'll be Your Factor", ["Factors and Multiples", "LCM and HCF Concepts"]),
            ("Can You See the Pattern?", ["Number Rules & Magic Squares", "Secret Code Patterns"]),
            ("Mapping Your Way", ["Scale Maps & Floor Plans", "Area Estimation on Grids"]),
            ("Boxes and Sketches", ["3D Cube Nets", "Isometric Sketches"]),
            ("Tenths and Hundredths", ["Decimals & Fractions Relation", "Metric Decimal Conversion"]),
            ("Area and its Boundary", ["Perimeter & Area Formulas", "Square Meter Word Problems"]),
            ("Smart Charts", ["Tally Marks & Bar Graphs", "Pie Charts Interpretation"]),
            ("How Big? How Heavy?", ["Volume of Cubes & Cuboids", "Water Displacement Experiments"])
        ],
        "English": [
            ("Unit 1: Treats & Waste", ["Ice-Cream Man", "Wonderful Waste!"]),
            ("Unit 2: Teamwork", ["Teamwork Rhyme", "Flying Together"]),
            ("Unit 3: Exploration", ["Robinson Crusoe Discovers a Footprint", "My Elder Brother"])
        ],
        "Hindi": [
            ("इकाई १: कहानियाँ", ["राख की रस्सी", "खिलौनेवाला"]),
            ("इकाई २: अनुभव", ["जहाँ चाह वहाँ राह", "डाकिए की कहानी"]),
            ("इकाई ३: यात्रा", ["एक दिन की बादशाहत", "चुनौती हिमालय की"])
        ],
        "EVS": [
            ("Super Senses & Food", ["Animal Super Senses", "Digestion & Food Preservation"]),
            ("Seeds & Water", ["Seed Germination & Dispersal", "Water Density & Dead Sea"]),
            ("Exploration", ["Bachendri Pal & Sunita Williams in Space", "Bhuj Earthquake & Natural Calamities"])
        ],
        "Computer": [
            ("Computer Generations", ["Generations of Computers", "MS Word Tables & Mail Merge"]),
            ("PowerPoint & Scratch", ["MS PowerPoint Slide Transitions", "Scratch Loops & Conditional Blocks"])
        ]
    },
    "6": {
        "Mathematics": [
            ("Knowing Our Numbers", ["Large Numbers Estimation & Brackets", "Roman Numerals"]),
            ("Whole Numbers", ["Properties of Whole Numbers", "Number Line Addition/Subtraction"]),
            ("Playing with Numbers", ["Prime & Composite Numbers", "HCF and LCM Applications"]),
            ("Basic Geometrical Ideas", ["Points, Lines, Rays, Segments", "Polygons, Triangles & Circles"]),
            ("Understanding Elementary Shapes", ["Measuring Angles & Triangles Classification", "3D Shapes Overview"]),
            ("Integers", ["Integers Representation", "Addition & Subtraction of Integers"]),
            ("Fractions", ["Types of Fractions", "Addition & Subtraction of Fractions"]),
            ("Decimals", ["Decimals Addition/Subtraction", "Decimals Applications"]),
            ("Data Handling", ["Tally Marks & Pictographs", "Bar Graphs Construction"]),
            ("Mensuration", ["Perimeter Formulas", "Area of Rectangles & Squares"]),
            ("Algebra", ["Variables & Constants", "Algebraic Expressions & Equations"]),
            ("Ratio and Proportion", ["Ratio Concept & Simplification", "Proportion & Unitary Method"])
        ],
        "Science": [
            ("Components of Food", ["Nutrients (Carbs, Proteins, Fats, Vitamins)", "Balanced Diet & Deficiency Diseases"]),
            ("Sorting Materials into Groups", ["Properties of Materials (Solubility, Transparency)", "Classification Exercises"]),
            ("Separation of Substances", ["Methods of Separation (Threshing, Winnowing, Filtration)", "Evaporation & Saturation"]),
            ("Getting to Know Plants", ["Herbs, Shrubs, Trees", "Root, Stem, Leaf & Leaf Venation", "Flower Structure & Photosynthesis"]),
            ("Body Movements", ["Human Skeleton & Joints", "Gait of Animals (Earthworm, Snail, Fish, Birds)"]),
            ("The Living Organisms & Surroundings", ["Habitats & Adaptations", "Biotic & Abiotic Components"]),
            ("Motion and Measurement of Distances", ["Standard Units of Measurement", "Types of Motion (Rectilinear, Circular, Periodic)"]),
            ("Light, Shadows and Reflections", ["Opaque, Transparent & Translucent Objects", "Shadow Formation & Pinhole Camera"]),
            ("Electricity and Circuits", ["Electric Cell & Bulb Circuit", "Conductors and Insulators"]),
            ("Fun with Magnets", ["Magnetic & Non-Magnetic Materials", "Poles of Magnet & Compass"]),
            ("Air Around Us", ["Composition of Air", "Importance of Oxygen Cycle"])
        ],
        "English": [
            ("Honeysuckle Unit 1", ["Who Did Patrick's Homework?", "A House, A Home"]),
            ("Honeysuckle Unit 2", ["How the Dog Found Himself a New Master!", "The Kite"]),
            ("Honeysuckle Unit 3", ["Taro's Reward", "An Indian-American Woman in Space: Kalpana Chawla"]),
            ("A Pact with the Sun Reader", ["A Tale of Two Birds", "The Friendly Mongoose", "The Shepherd's Treasure"])
        ],
        "Social Science": [
            ("History: Early Civilizations", ["What, Where, How and When?", "From Gathering to Growing Food", "In the Earliest Cities (Harappa)"]),
            ("History: Empires", ["What Books and Burials Tell Us", "Kingdoms, Kings & Early Republic", "Ashoka, The Emperor Who Gave Up War"]),
            ("Geography: Earth & Solar System", ["The Earth in the Solar System", "Globe: Latitudes and Longitudes", "Motions of the Earth", "Maps"]),
            ("Civics: Democracy & Governance", ["Understanding Diversity", "Diversity and Discrimination", "What is Government?", "Panchayati Raj & Urban Admin"])
        ],
        "Hindi": [
            ("वसंत भाग १", ["वह चिड़िया जो", "बचपन", "नादान दोस्त", "चाँद से थोड़ी सी गप्पें"]),
            ("बाल रामकथा", ["अवधपुरी में राम", "जंगल और जनकपुर", "दो वरदान", "राम का वन-गमन"])
        ],
        "Sanskrit": [
            ("रुचिरा प्रथमो भागः", ["शब्दपरिचयः I (अकारान्त पुंल्लिङ्ग)", "शब्दपरिचयः II (आकारान्त स्त्रीलिङ्ग)", "विद्यालयः", "वृक्षाः", "बकस्य प्रतीकारः"])
        ],
        "Computer": [
            ("Computer Science & AI", ["Binary Number System Conversion", "MS Excel SUM, AVERAGE & Formulas"]),
            ("Web & Coding", ["HTML5 Webpage Tags", "Python Programming Syntax & Variables", "Intro to Artificial Intelligence & Computer Vision"])
        ]
    },
    "7": {
        "Mathematics": [
            ("Integers", ["Properties of Addition & Subtraction", "Multiplication & Division of Integers"]),
            ("Fractions and Decimals", ["Multiplication & Division of Fractions", "Decimals Operations"]),
            ("Data Handling", ["Mean, Median, Mode", "Double Bar Graphs & Probability"]),
            ("Simple Equations", ["Setting up Equations", "Solving Equations"]),
            ("Lines and Angles", ["Related Angles (Complementary/Supplementary)", "Pairs of Lines & Transversals"]),
            ("The Triangle and its Properties", ["Medians & Altitudes", "Exterior Angle & Pythagoras Theorem"]),
            ("Comparing Quantities", ["Ratios & Percentages", "Profit & Loss, Simple Interest"]),
            ("Rational Numbers", ["Rational Numbers Properties", "Operations on Rational Numbers"]),
            ("Algebraic Expressions", ["Terms, Factors & Coefficients", "Addition & Subtraction of Expressions"]),
            ("Exponents and Powers", ["Laws of Exponents", "Decimal Number System & Standard Form"])
        ],
        "Science": [
            ("Nutrition in Plants", ["Mode of Nutrition & Photosynthesis", "Other Modes of Nutrition in Plants"]),
            ("Nutrition in Animals", ["Digestive System in Humans", "Digestion in Grass-Eating Animals"]),
            ("Heat", ["Hot and Cold & Thermometer", "Transfer of Heat (Conduction, Convection, Radiation)"]),
            ("Acids, Bases and Salts", ["Indicators (Litmus, Turmeric)", "Neutralisation in Everyday Life"]),
            ("Physical and Chemical Changes", ["Physical Changes Examples", "Chemical Reactions & Rusting"]),
            ("Respiration in Organisms", ["Aerobic & Anaerobic Respiration", "Breathing Mechanism in Humans"]),
            ("Transportation in Animals and Plants", ["Circulatory System (Blood, Blood Vessels, Heart)", "Transport of Water & Nutrients"]),
            ("Reproduction in Plants", ["Asexual Reproduction (Vegetative Propagation)", "Sexual Reproduction & Pollination"]),
            ("Motion and Time", ["Speed Calculation", "Measurement of Time & Distance-Time Graphs"]),
            ("Electric Current and its Effects", ["Symbols of Electric Components", "Heating & Magnetic Effect of Current"]),
            ("Light", ["Reflection of Light", "Spherical Mirrors & Lenses Overview"])
        ],
        "Social Science": [
            ("History: Medieval India", ["Tracing Changes Through 1000 Years", "New Kings and Kingdoms", "The Delhi Sultans", "The Mughal Empire"]),
            ("Geography: Environment", ["Environment Components", "Inside Our Earth & Changing Earth", "Air & Water Systems"]),
            ("Civics: Equality & State", ["On Equality", "Role of Government in Health", "How the State Government Works"])
        ]
    },
    "8": {
        "Mathematics": [
            ("Rational Numbers", ["Closure, Commutative & Associative Properties", "Representation on Number Line"]),
            ("Linear Equations in One Variable", ["Solving Equations with Variables on Both Sides", "Applications"]),
            ("Understanding Quadrilaterals", ["Polygons Properties", "Types of Quadrilaterals (Parallelogram, Rhombus, Trapezium)"]),
            ("Data Handling", ["Bar Graphs & Pie Charts", "Probability Introduction"]),
            ("Squares and Square Roots", ["Square Numbers Properties", "Square Roots by Prime Factorization & Division"]),
            ("Cubes and Cube Roots", ["Cube Numbers", "Cube Root Calculations"]),
            ("Comparing Quantities", ["Discount & Sales Tax/GST", "Compound Interest Formula & Applications"]),
            ("Algebraic Expressions and Identities", ["Standard Algebraic Identities", "Applying Identities"]),
            ("Mensuration", ["Area of Trapezium & Polygons", "Surface Area & Volume of Cube, Cuboid, Cylinder"]),
            ("Exponents and Powers", ["Powers with Negative Exponents", "Laws of Exponents & Standard Form"]),
            ("Direct and Inverse Proportions", ["Direct Proportion Concept", "Inverse Proportion Applications"]),
            ("Factorisation", ["Factorisation by Regrouping & Identities", "Division of Algebraic Expressions"])
        ],
        "Science": [
            ("Crop Production and Management", ["Agricultural Practices (Soil Prep, Sowing)", "Irrigation, Harvesting & Storage"]),
            ("Microorganisms: Friend and Foe", ["Types of Microorganisms", "Harmful Effects & Food Preservation"]),
            ("Coal and Petroleum", ["Exhaustible Natural Resources", "Petroleum Refining & Fossil Fuels"]),
            ("Combustion and Flame", ["Conditions for Combustion", "Structure of Flame & Fuel Efficiency"]),
            ("Conservation of Plants and Animals", ["Deforestation & Consequences", "Biosphere Reserves & Wildlife Sanctuaries"]),
            ("Reproduction in Animals", ["Modes of Reproduction", "Fertilization (Internal & External)"]),
            ("Reaching the Age of Adolescence", ["Adolescence & Puberty Changes", "Hormones & Reproductive Health"]),
            ("Force and Pressure", ["Push and Pull Forces", "Contact & Non-Contact Forces", "Atmospheric Pressure"]),
            ("Friction", ["Factors Affecting Friction", "Advantages & Disadvantages of Friction"]),
            ("Sound", ["Production & Propagation of Sound", "Audible & Inaudible Sounds, Noise Pollution"]),
            ("Chemical Effects of Electric Current", ["Conducted Liquids", "Electroplating Applications"]),
            ("Light", ["Laws of Reflection", "Human Eye & Care"])
        ],
        "Social Science": [
            ("History: Modern India", ["How, When and Where", "From Trade to Territory", "Ruling the Countryside", "When People Rebel (1857)"]),
            ("Geography: Resources", ["Types of Resources", "Land, Soil, Water, Natural Vegetation", "Agriculture & Industries"]),
            ("Civics: Constitution", ["The Indian Constitution", "Understanding Secularism", "Why Do We Need a Parliament?", "The Judiciary"])
        ]
    },
    "9": {
        "Mathematics": [
            ("Number Systems", ["Irrational Numbers & Real Numbers", "Real Numbers Operations & Rationalization"]),
            ("Polynomials", ["Zeroes of a Polynomial", "Remainder & Factor Theorems", "Algebraic Identities"]),
            ("Coordinate Geometry", ["Cartesian Plane & Coordinates", "Plotting Points"]),
            ("Linear Equations in Two Variables", ["Linear Equations Solutions", "Graph of Linear Equations"]),
            ("Introduction to Euclid's Geometry", ["Euclid's Definitions & Axioms", "Postulates"]),
            ("Lines and Angles", ["Intersecting & Parallel Lines", "Angle Sum Property of a Triangle"]),
            ("Triangles", ["Congruence Criteria (SAS, ASA, SSS, RHS)", "Inequalities in a Triangle"]),
            ("Quadrilaterals", ["Mid-point Theorem", "Properties of Parallelograms"]),
            ("Circles", ["Perpendicular from Centre to Chord", "Angles Subtended by Arcs"]),
            ("Heron's Formula", ["Area of Triangle using Heron's Formula", "Applications"]),
            ("Surface Areas and Volumes", ["Surface Area & Volume of Sphere & Hemispheres", "Right Circular Cones"]),
            ("Statistics", ["Bar Graphs, Histograms & Frequency Polygons", "Measures of Central Tendency"])
        ],
        "Science": [
            ("Matter in Our Surroundings", ["Physical Nature of Matter", "States of Matter & Evaporation"]),
            ("Is Matter Around Us Pure?", ["Elements, Compounds & Mixtures", "Solutions, Suspensions & Colloids"]),
            ("Atoms and Molecules", ["Laws of Chemical Combination", "Atomic Mass & Mole Concept"]),
            ("Structure of the Atom", ["Thomson, Rutherford & Bohr Models", "Valency & Atomic Number"]),
            ("The Fundamental Unit of Life", ["Cell Organelles & Cell Membrane", "Mitosis vs Meiosis"]),
            ("Tissues", ["Plant Tissues (Meristematic & Permanent)", "Animal Tissues (Epithelial, Connective, Muscular, Nervous)"]),
            ("Motion", ["Speed, Velocity & Acceleration", "Graphical Equations of Motion"]),
            ("Force and Laws of Motion", ["First, Second & Third Laws of Motion", "Momentum Conservation"]),
            ("Gravitation", ["Universal Law of Gravitation", "Free Fall, Mass & Weight, Buoyancy"]),
            ("Work and Energy", ["Work Done by Constant Force", "Kinetic & Potential Energy, Power"]),
            ("Sound", ["Production & Propagation of Sound Wave", "Echo & Ultrasound Applications"])
        ],
        "AI (Subject Code 417)": [
            ("AI Project Cycle", ["Problem Scoping, Data Acquisition, Data Exploration", "Modelling & Evaluation"]),
            ("Python Programming", ["Lists, Tuples, Dictionaries & Functions", "Packages: NumPy & Pandas Intro"]),
            ("Neural Networks", ["Perceptrons & Artificial Neural Networks", "Ethical AI Considerations"])
        ]
    },
    "10": {
        "Mathematics": [
            ("Real Numbers", ["Fundamental Theorem of Arithmetic", "Revisiting Irrational Numbers Proofs"]),
            ("Polynomials", ["Geometrical Meaning of Zeroes", "Relationship between Zeroes & Coefficients"]),
            ("Pair of Linear Equations in Two Variables", ["Graphical Method", "Algebraic Methods (Substitution & Elimination)"]),
            ("Quadratic Equations", ["Standard Form & Factorisation", "Quadratic Formula & Nature of Roots"]),
            ("Arithmetic Progressions", ["nth Term of an AP", "Sum of First n Terms of AP"]),
            ("Triangles", ["Basic Proportionality Theorem (Thales)", "Criteria for Similarity of Triangles"]),
            ("Coordinate Geometry", ["Distance Formula", "Section Formula & Mid-point"]),
            ("Introduction to Trigonometry", ["Trigonometric Ratios", "Trigonometric Identities"]),
            ("Some Applications of Trigonometry", ["Heights and Distances Problems", "Angle of Elevation & Depression"]),
            ("Circles", ["Tangent to a Circle Theorem", "Number of Tangents from a Point"]),
            ("Areas Related to Circles", ["Area of Sector & Segment of Circle", "Combination of Plane Figures"]),
            ("Surface Areas and Volumes", ["Surface Area of Combination of Solids", "Volume of Combination of Solids"]),
            ("Statistics", ["Mean, Median, Mode of Grouped Data", "Cumulative Frequency Ogives"]),
            ("Probability", ["Classical Approach to Probability", "Simple Event Calculations"])
        ],
        "Science": [
            ("Chemical Reactions and Equations", ["Balancing Chemical Equations", "Types of Chemical Reactions"]),
            ("Acids, Bases and Salts", ["Chemical Properties of Acids & Bases", "pH Scale & Salts Preparation"]),
            ("Metals and Non-metals", ["Physical & Chemical Properties", "Reactivity Series & Metallurgy"]),
            ("Carbon and its Compounds", ["Covalent Bonding & Versatile Nature of Carbon", "Homologous Series & Functional Groups"]),
            ("Life Processes", ["Nutrition (Autotrophic & Heterotrophic)", "Respiration, Transportation & Excretion"]),
            ("Control and Coordination", ["Nervous System & Reflex Arc", "Plant Hormones & Endocrine System"]),
            ("How do Organisms Reproduce?", ["Asexual Reproduction Modes", "Sexual Reproduction in Flowering Plants & Humans"]),
            ("Heredity and Evolution", ["Mendel's Experiments & Monohybrid Cross", "Sex Determination in Humans"]),
            ("Light – Reflection and Refraction", ["Mirror Formula & Magnification", "Refraction & Lens Formula"]),
            ("The Human Eye and the Colorful World", ["Defects of Vision & Correction", "Dispersion & Atmospheric Refraction"]),
            ("Electricity", ["Ohm's Law & Resistance", "Resistors in Series & Parallel, Electric Power"]),
            ("Magnetic Effects of Electric Current", ["Magnetic Field Lines", "Right-Hand Thumb Rule & Solenoid"])
        ],
        "AI (Subject Code 417)": [
            ("Advance Python", ["Object Oriented Programming Basics", "Data Analysis with Pandas"]),
            ("Computer Vision", ["Image Processing Fundamentals", "OpenCV Basics & Convolutional Neural Nets"]),
            ("Natural Language Processing", ["Text Processing & Tokenization", "Bag of Words & TF-IDF Vectorization"])
        ]
    },
    "11": {
        "Physics": [
            ("Physical World and Measurement", ["Units and Dimensions", "Dimensional Analysis & Errors"]),
            ("Kinematics", ["Motion in a Straight Line", "Motion in a Plane & Projectile Motion"]),
            ("Laws of Motion", ["Newton's Laws & Inertia", "Friction & Circular Motion"]),
            ("Work, Energy and Power", ["Work-Energy Theorem", "Collisions (Elastic & Inelastic)"]),
            ("System of Particles and Rotational Motion", ["Center of Mass", "Torque & Angular Momentum"]),
            ("Gravitation", ["Kepler's Laws & Escape Velocity", "Gravitational Potential Energy"]),
            ("Thermodynamics", ["First Law of Thermodynamics", "Heat Engines & Second Law"])
        ],
        "Chemistry": [
            ("Some Basic Concepts of Chemistry", ["Mole Concept & Stoichiometry", "Empirical & Molecular Formula"]),
            ("Structure of Atom", ["Bohr's Model & Quantum Numbers", "Electronic Configuration"]),
            ("Chemical Bonding and Molecular Structure", ["Ionic & Covalent Bonds", "VSEPR Theory & Hybridisation"]),
            ("Chemical Thermodynamics", ["Enthalpy, Entropy & Gibbs Free Energy", "Hess's Law"]),
            ("Organic Chemistry: Basic Principles", ["IUPAC Nomenclature", "Isomerism & Reaction Mechanisms"])
        ],
        "Mathematics": [
            ("Sets and Functions", ["Sets Operations & Venn Diagrams", "Relations and Functions"]),
            ("Trigonometric Functions", ["Trigonometric Equations", "Compound Angle Formulas"]),
            ("Calculus: Limits and Derivatives", ["Limits Evaluation", "Derivatives of Polynomials & Trig Functions"]),
            ("Linear Inequalities & Permutations", ["Graphical Solution of Inequalities", "Permutations & Combinations Formulas"])
        ]
    },
    "12": {
        "Physics": [
            ("Electrostatics", ["Electric Charges & Coulomb's Law", "Electric Field & Gauss's Law", "Capacitance"]),
            ("Current Electricity", ["Ohm's Law & Kirchhoff's Rules", "Wheatstone Bridge & Potentiometer"]),
            ("Magnetic Effects of Current and Magnetism", ["Biot-Savart Law & Ampere's Law", "Cyclotron & Magnetic Dipole"]),
            ("Electromagnetic Induction and AC", ["Faraday's Law & Lenz's Law", "AC Generator & Transformers"]),
            ("Optics", ["Ray Optics & Lenses Formula", "Wave Optics & Interference/Diffraction"]),
            ("Modern Physics", ["Dual Nature of Radiation", "Atoms, Nuclei & Semiconductor Devices"])
        ],
        "Chemistry": [
            ("Solutions", ["Raoult's Law & Colligative Properties", "Abnormal Molar Mass"]),
            ("Electrochemistry", ["Nernst Equation & Conductance", "Kohlrausch's Law & Fuel Cells"]),
            ("Chemical Kinetics", ["Rate of Reaction & Order", "Arrhenius Equation"]),
            ("Organic Chemistry: Haloalkanes to Biomolecules", ["SN1 & SN2 Mechanisms", "Alcohols, Aldehydes & Carboxylic Acids", "Proteins, Nucleic Acids & Polymers"])
        ],
        "Mathematics": [
            ("Relations and Functions & Inverse Trig", ["Types of Relations & Functions", "Inverse Trigonometric Formulas"]),
            ("Matrices and Determinants", ["Matrix Operations & Inverse", "Determinants Properties & Cramer's Rule"]),
            ("Calculus: Continuity & Differentiability", ["Continuity Checks", "Chain Rule & Implicit Differentiation"]),
            ("Calculus: Integrals & Applications", ["Definite & Indefinite Integrals", "Area Under Curves"]),
            ("Vectors and 3D Geometry", ["Vector Algebra & Dot/Cross Product", "Line & Plane Equations in 3D"]),
            ("Linear Programming & Probability", ["LPP Graphical Method", "Conditional Probability & Bayes' Theorem"])
        ]
    }
}


def seed_cbse_curriculum_data(school_id=None):
    """
    Seeds authentic CBSE curriculum classes (Class 1 to Class 12), subjects, chapters, and topics into DB.
    """
    sch_id = school_id or 1
    sess = AcademicSession.query.filter_by(is_active=True).first() or AcademicSession.query.order_by(AcademicSession.id.desc()).first()
    sess_id = sess.id if sess else 1

    created_classes_cnt = 0
    created_subjects_cnt = 0
    created_chapters_cnt = 0
    created_topics_cnt = 0

    for grade_code, subjects_map in CBSE_CURRICULUM_DATA.items():
        # Ensure Class exists
        class_name = f"{grade_code}th" if int(grade_code) >= 4 else (f"{grade_code}st" if grade_code == "1" else (f"{grade_code}nd" if grade_code == "2" else f"{grade_code}rd"))
        cls = SchoolClass.query.filter((SchoolClass.name == class_name) | (SchoolClass.name == grade_code) | (SchoolClass.name == f"Class {class_name}")).first()
        if not cls:
            cls = SchoolClass(
                name=class_name,
                code=f"CLS-{grade_code}",
                academic_session_id=sess_id
            )
            db.session.add(cls)
            db.session.commit()
            created_classes_cnt += 1

        for subj_name, chapters_list in subjects_map.items():
            # Ensure Subject exists
            subj_code = f"{subj_name[:4].upper()}{grade_code}"
            subj = Subject.query.filter_by(name=subj_name).first()
            if not subj:
                subj = Subject(name=subj_name, code=subj_code, subject_type="Theory")
                db.session.add(subj)
                db.session.commit()
                created_subjects_cnt += 1

            # Seed chapters and topics
            for ch_idx, (ch_title, topics_list) in enumerate(chapters_list, start=1):
                chapter = SyllabusChapter.query.filter_by(class_id=cls.id, subject_id=subj.id, chapter_number=ch_idx).first()
                if not chapter:
                    chapter = SyllabusChapter(
                        school_id=sch_id,
                        academic_session_id=sess_id,
                        class_id=cls.id,
                        subject_id=subj.id,
                        chapter_name=ch_title,
                        chapter_number=ch_idx,
                        display_order=ch_idx
                    )
                    db.session.add(chapter)
                    db.session.commit()
                    created_chapters_cnt += 1

                for t_idx, t_name in enumerate(topics_list, start=1):
                    topic = SyllabusTopic.query.filter_by(chapter_id=chapter.id, topic_name=t_name).first()
                    if not topic:
                        topic = SyllabusTopic(
                            school_id=sch_id,
                            chapter_id=chapter.id,
                            topic_name=t_name,
                            display_order=t_idx,
                            teaching_status="NOT_STARTED"
                        )
                        db.session.add(topic)
                        created_topics_cnt += 1

    db.session.commit()
    return {
        "classes": created_classes_cnt,
        "subjects": created_subjects_cnt,
        "chapters": created_chapters_cnt,
        "topics": created_topics_cnt
    }
