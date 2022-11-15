# Persona Generation System
[Link](http://103.238.162.32:8501/%E4%BA%BA%E8%AE%BE%E7%94%9F%E6%88%90)

This page allows all users to access. You can:

- Choose a persona version and talk with it

- Generate the question-answering pair of specific types to help build the persona

`persona_{API_VERSION}` collection:

| id           | persona | type         | tag                                 | query                    | answer                                                       | candidates                              |
| ------------ | ------- | ------------ | ----------------------------------- | ------------------------ | ------------------------------------------------------------ | --------------------------------------- |
| 这条数据的id | 人格    | 问题的类型   | 标签(比如，情绪的细分类,逻辑类型等) | 对话的问题               | 依据人格做出的合理回答                                       | glm在sample中产生的候选                 |
| 例子:        |         |              |                                     |                          |                                                              |                                         |
| 1            | 学姐    | introduction | 1                                   | 你好                     | 同学你好，我是你的学姐小木~                                  | [ \] (这个初始介绍一般是手写的)         |
| 2            | 学姐    | emotion      | nervous                             | 找不到实习好焦虑         | 小木理解你,我有很多朋友都是研究生,他们也在焦虑这个,所以别担心啦 | ['小木也是找不到实习呢','来我这实习吧'] |
| 3            | 学姐    | logic        | compare                             | 学计算机还是物理专业好呢 | (计算机是...)(物理是...)，二者都不错呢，看你的兴趣咯         | ['...我不知道']                         |



# Persona Management System

[Link](http://103.238.162.32:8501/%E4%BA%BA%E8%AE%BE%E7%AE%A1%E7%90%86)

This page only allows super user to access. You can:

- Delete the QA pair record from Persona Generation System

- Select several QA records to build a new version's persona

`pid_list_{API_VERSION}` collection:

| _id                      | vid                             | pid_list                                                     |
| ------------------------ | ------------------------------- | ------------------------------------------------------------ |
| MongoDB生成的id          | 这条数据的id (`人设_用户_第几`) | 此版本需要用到的QA对在persona表中的_id集合                   |
| 例子:                    |                                 |                                                              |
| 6370f9434d7c7afac16e5536 | 学姐_tsq22_0                    | ['636f0de46965dee87bd0827a', '636f1279bd33b0a82ca8a97e', '636f12dbbd33b0a82ca8a986', '636f131dbd33b0a82ca8a98a', '636f562282bf84d6635a80c3', '636f5d552297abf5ceee605a', '6370472af9a8e7ce20c75663', '63704740f9a8e7ce20c75667', '63704781f9a8e7ce20c7566e', '637047b6f9a8e7ce20c75674', '63704b40177114d4ed321f8a'] |
| 6370f9de413400b2511d4d87 | 学姐_tsq22_1                    | ['636f0de46965dee87bd0827a', '636f1279bd33b0a82ca8a97e', '636f12dbbd33b0a82ca8a986', '636f131dbd33b0a82ca8a98a', '636f5d552297abf5ceee605a', '637047b6f9a8e7ce20c75674'] |
