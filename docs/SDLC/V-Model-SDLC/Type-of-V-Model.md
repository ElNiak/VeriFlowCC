# Using V Models for Testing

The [verification and validation](https://en.wikipedia.org/wiki/Verification_and_validation) of [requirements](https://en.wikipedia.org/wiki/Requirement) are a critical part of [systems](https://en.wikipedia.org/wiki/Systems_engineering) and [software engineering](https://en.wikipedia.org/wiki/Software_engineering). The importance of verification and validation (especially [testing](https://en.wikipedia.org/wiki/Software_testing)) is a major reason that the [traditional waterfall development cycle](https://en.wikipedia.org/wiki/Waterfall_model) underwent a minor modification to create the [V model](https://en.wikipedia.org/wiki/V-Model_%28software_development%29) that links early development activities to their corresponding later testing activities. This blog post introduces three variants on the V model of system or software development that make it more useful to testers, quality engineers, and other stakeholders interested in the use of testing as a verification and validation method.

**The Traditional V Model**

Verification and validation are typically performed using one or more of the following four techniques:

- [**analysis**](https://en.wikipedia.org/wiki/Analysis)--the use of established technical or mathematical models, simulations, algorithms, or scientific principles and procedures to determine whether a work product meets its requirements
- [**demonstration**](https://en.wikipedia.org/wiki/Technology_demonstration)--the visual examination of the execution of a work product under specific scenarios to determine whether it meets its requirements
- [**inspection**](https://en.wikipedia.org/wiki/Inspection)--the visual examination (possibly including physical manipulation or the use of simple mechanical or electrical measurement) of a non-executing work product to determine whether it meets its requirements
- [**testing**](https://en.wikipedia.org/wiki/Software_testing)--the stimulation of an executable work product with known inputs and preconditions followed by the comparison of its actual with required response (outputs and postconditions) to determine whether it meets its requirements

The [V model](https://en.wikipedia.org/wiki/V-Model_%28software_development%29) is a simple variant of [the traditional waterfall model](https://en.wikipedia.org/wiki/Waterfall_development) of system or software development. As illustrated in Figure 1, the V model builds on the waterfall model by emphasizing verification and validation. The V model takes the bottom half of the waterfall model and bends it upward into the form of a V, so that the activities on the right verify or validate the work products of the activity on the left. More specifically, the left side of the V represents the analysis activities that decompose the users' needs into small, manageable pieces, while the right side of the V shows the corresponding synthesis activities that aggregate (and test) these pieces into a system that meets the users' needs.

[![F1 - Traditional V Model.jpg](/media/images/F1_-_Traditional_V_Model.max-1280x720.format-webp.webp)](/media/images/F1_-_Traditional_V_Model.original.jpg)

Traditional Single V Model of System Engineering Activities

##### Figure 1: Traditional Single V Model of System Engineering Activitie. To view a larger version of this model, please click on the image.

Like the waterfall model, the V model has both advantages and disadvantages. On the positive side, it clearly represents the primary engineering activities in a logical flow that is easily understandable and balances development activities with their corresponding testing activities. On the other hand, the V model is a gross oversimplification in which these activities are illustrated as sequential phases rather than activities that typically occur incrementally, iteratively, and concurrently, especially on projects using evolutionary (agile) development approaches.

Software developers can lessen the impact of this sequential phasing limitation if they view development as consisting of many short-duration V's rather than a small number of large V's, one for each concurrent iterative increment. When programmers apply a V model to the [agile development](https://en.wikipedia.org/wiki/Agile_software_development) of a large, complex system, however, they encounter some potential complications that require more than a simple collection of small V models including the following:

- The architecturally significant requirements and associated architecture must be engineered and stabilized as rapidly as is practical. All subsequent increments depend on the architecture, which becomes hard--and expensive--to modify after the initial increments have been based on it.
- Multiple, cross-functional agile teams will be working on different components and subsystems simultaneously, so their increments must be coordinated across teams to produce consistent, testable components and subsystems that can be integrated and released.

Another problem with the V model is that the distinction between [unit](https://en.wikipedia.org/wiki/Unit_testing), [integration](https://en.wikipedia.org/wiki/Integration_testing), and [system testing](https://en.wikipedia.org/wiki/System_testing) is not as clear cut as the model implies. For instance, a certain number of test cases can sometimes be viewed as both unit and integration tests, thereby avoiding redundant development of the associated test inputs, test outputs, test data, and test scripts. Nevertheless, the V model is still a useful way of thinking about development as long as everyone involved (especially management) remembers that it is merely a simplifying abstraction and not intended to be a complete and accurate model of modern system or software development.

Many testers still use the traditional V model because they are not familiar with the following V models that are more appropriate for testing.

**V Models from the Tester's Point of View**

While a useful if simplistic model of system or software development, the traditional V model does not adequately capture development from the tester's point of view. This blog discusses three variations of the traditional V model of system/software development that make it more useful to testers, quality engineers, and other stakeholders interested in the use of testing as a verification and validation method.

- **The single V model** modifies the nodes of the traditional V model to represent the executable work products to be tested rather than the activities used to produce them.
- **The double V model** adds a second V to show the type of tests corresponding to each of these executable work products.
- **The triple V model** adds a third V to illustrate the importance of verifying the tests to determine whether they contain defects that could stop or delay testing or lead to false positive or false negative test results.

As mentioned above, testing is a major verification technique intended to determine whether an executable work product behaves as expected or required when stimulated with known inputs. Testers test these work products by placing them into known pretest states (preconditions), stimulating them with appropriate inputs (data, messages, and exceptions), and comparing the actual results (postconditions and outputs) with the expected or required results to find faults and failures that can lead to underlying defects.

Figure 2 shows the tester's single V model, which is oriented around these work products rather than the activities that produce them. In this case, the left side of the V illustrates the analysis of ever more detailed executable models, whereas the right side illustrates the corresponding incremental and iterative synthesis of the actual system. Thus, this V model shows the executable work products that are tested rather than the general system engineering activities that generate them.

[![F2 - Executable Work Product V Model.jpg](/media/images/F2_-_Executable_Work_Product_V.max-1280x720.format-webp.webp)](/media/images/F2_-_Executable_Work_Product_V_Model.original.jpg)

Figure 2: Tester's Single V Model of Testable Work Products

##### Figure 2: Tester's Single V Model of Testable Work Products. To view a larger version of this model, please click on the image.

**The Tester's Double V Model**

Traditionally, only the right side of the V model dealt with testing. The requirements, architecture, and design work products on the left side of the model have been documents and informal diagrams that were best verified by such manual verification techniques as analysis, inspections, and reviews. With the advent of [model-based development](https://en.wikipedia.org/wiki/Model-driven_software_development), the requirements, architecture, and design models became better defined by using more formally defined [modeling languages](https://en.wikipedia.org/wiki/Modeling_languages), and it became possible to use automated tools that implement static analysis techniques to verify these models. More recently, further advances in modeling languages and associated tools have resulted in executable models that can actually be tested by stimulating the executable models with test inputs and comparing actual with expected behavior.

Figure 3 shows the Tester's double-V model, which adds the corresponding tests to the tester's single V model. The double V model allows us to detect and fix defects in the work products on left side of the V before they can flow into the system and its components on the right side of the V.

In the double V model, every executable work product should be tested. Testing need not--and in fact should not--be restricted to the implemented system and its parts. It is also important to test any executable requirements, architecture, and design so that the defects in the models are found and fixed before they can migrate to the actual system and its parts. This process typically involves testing an executable requirements, architecture, or design model (or possibly a prototype) that

- is implemented in a modeling language (often state-based) such as [SpecTRM Requirements Language (SpecTRM-RL)](http://www.safeware-eng.com/software%20safety%20products/features.htm), [Architecture Analysis and Design Language (AADL)](/blog/?tag=architecture-analysis-design-language-aadl), and [Program Design Language (PDL)](https://en.wikipedia.org/wiki/Program_Design_Language)
- is sufficiently formal to be executable using an appropriate associated tool
- simulates the system under test

Tests should be created and performed as the corresponding work products are created. In Figure 3, the short arrows with two arrowheads are used to show that (1) the executable work products can be developed first and used to drive the creation of the tests or (2) [test driven development (TDD)](https://en.wikipedia.org/wiki/Test-driven_development) can be used, in which case the tests are developed before the work product they test.

The top row of the model uses testing to validate that the system meets the needs of its stakeholders (that is, that the correct system is built). Conversely, the bottom four rows of the model use testing to verify that the system is built correctly (that is, architecture conforms to requirements, design conforms to architecture, implementation conforms to design, and so on).

In addition to the standard double V model, there are two variants that deserve mention.

- There is little reason to perform unit testing if [model-driven development (MDD)](https://en.wikipedia.org/wiki/Model-driven_engineering) is used, a trusted tool is used to automatically generate the units from the unit design, and unit design testing has been performed and passed.
- Similarly, there is little reason to perform separate unit design testing if the unit design has been incorporated into the unit using the programming language as a [program design language (PDL)](https://en.wikipedia.org/wiki/Program_Design_Language) so that unit testing verifies both the unit's design and implementation.

[![F3 - Double V Model.jpg](/media/images/F3_-_Double_V_Model.max-1280x720.format-webp.webp)](/media/images/F3_-_Double_V_Model.original.jpg)

Figure 3: Tester's Double V Model of Testable Work Products and Corresponding Tests

##### Figure 3: Tester's Double V Model of Testable Work Products and Corresponding Test. To view a larger version of this model, please click on the image.

**The Tester's Triple V Model**

The final variant of the traditional V model, the triple V model, consists of three interwoven V models. The left V model shows the main executable work products that must be tested. The middle V model shows the types of tests that are used to verify and validate these work products. The right V model shows the verification of these testing work products in the middle V. The triple V model uses the term verification rather than tests because the tests are most often verified by analysis, inspection, and review.

Figure 4 below documents the tester's triple V model, in which additional verification activities have been added to determine whether the testing work products are sufficiently complete and correct that they will not produce numerous false-positive and false-negative results.

[![F4 - Triple V Model.jpg](/media/images/F4_-_Triple_V_Model.max-1280x720.format-webp.webp)](/media/images/F4_-_Triple_V_Model.original.jpg)

Figure 4: The Tester's Triple V Model of Work Products, Tests, and Test Verification

##### Figure 4: The Tester's Triple V Model of Work Products, Tests, and Test Verification. To view a larger version of this model, please click on the image.

**Conclusion**

As we have demonstrated above, relatively minor changes to the traditional V model make it far more useful to testers. Modifying the traditional V model to show executable work products instead of the associated development activities that produce them, emphasizes that these are the work products that testers will test.

By associating each of these executable work products with its associated tests, the double V model makes it clear that testing does not have to wait until the right side of the V. Advances in the production of executable requirements, architectures, and designs enable testing to begin much earlier on the left side of the V so that requirements, architecture, and design defects can be found and fixed early before they can propagate into downstream work products.

Finally, the triple V model makes it clear that it is not just the primary work products that must be verified. The tests themselves should be deliverables and must be verified to ensure that defects in the tests do not invalidate the test results by causing false-positive and false-negative test results.

The V models have typically been used to describe the development of the system and its subsystems. The test environments or beds and test laboratories and facilities are also systems, however, and must be tested and otherwise verified. Thus, these test-oriented V models are applicable to them as well.

This blog entry has been adapted from chapter one of my book [_Common System and Software Testing Pitfalls_](https://www.amazon.com/Common-Testing-Pitfalls-Prevent-Mitigate/dp/0133748553/ref=sr_1_2), which will be published this December by Addison Wesley as part of the SEI Series in Software Engineering.

I would welcome your feedback on these suggested variations of the traditional V model in the comments section below.

**Additional Resources**

To read the SEI technical report, _Reliability Validation and Improvement Framework_ by Peter Feiler, John Goodenough, Arie Gurfinkel, Charles Weinstock, and Lutz Wrage, please visit
[https://resources.sei.cmu.edu/library/asset-view.cfm?assetid=34069](https://resources.sei.cmu.edu/library/asset-view.cfm?assetid=34069).
