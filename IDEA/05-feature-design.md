# Feature Design

Day la cac tinh nang nen phat trien dua tren logic Learning Graph.

## 1. Graph-Based Dashboard

Dashboard khong chi hien documents, ma hien:

- so node,
- so relationship,
- so module,
- so practice items,
- tien do hoc,
- node dang yeu,
- lich on tap hom nay.

## 2. Learning Graph View

Graph can co cac che do xem:

- **Knowledge View**: concept/fact/procedure.
- **Prerequisite View**: chi hien quan he `requires`.
- **Module View**: gom node theo module/community.
- **Practice View**: hien cau hoi/flashcard gan voi node.
- **Mastery View**: mau node theo muc do thanh thao.

## 3. Node Detail Panel

Khi click node, panel nen co:

- dinh nghia/giai thich,
- source citation,
- prerequisite nodes,
- related nodes,
- examples,
- common mistakes,
- quiz/flashcards,
- nut "Explain deeper",
- nut "Test me",
- nut "Review source".

## 4. AI Tutor

Tutor nen co nhieu mode:

```text
Ask Document
Ask Concept
Explain Like Beginner
Compare Concepts
Generate Example
Test Me
Find My Gap
```

Khac chatbot thuong: AI tutor phai biet graph va mastery cua user.

## 5. Learning Path

App tao learning path tu graph.

Input:

- subject,
- goal,
- thoi gian hoc,
- trinh do,
- mastery hien tai.

Output:

- danh sach module,
- node can hoc,
- thu tu hoc,
- uoc luong thoi gian,
- vi sao nen hoc node nay.

## 6. Practice Generation

Moi node nen tao duoc:

- flashcard,
- MCQ,
- short answer,
- cloze,
- explain prompt,
- exercise.

Practice nen co source_ref de nguoi hoc xem lai tai lieu.

## 7. Mastery Tracking

Moi node co mastery state:

```text
new
learning
weak
review
mastered
```

Update dua tren:

- so lan dung/sai,
- do kho cau hoi,
- thoi gian tra loi,
- kha nang giai thich lai,
- lich su on tap.

## 8. Spaced Repetition

Nen dung FSRS thay vi tu viet scheduler don gian.

Workflow:

```text
Practice item answered
-> grade answer
-> update FSRS state
-> set next_review_at
-> show in daily review
```

## 9. Knowledge Gap Detection

Neu user sai node B, app kiem tra:

- B requires A nao?
- User da mastered A chua?
- Sai cung type cau hoi nao?
- Co misconception nao lien quan?

Output:

```text
Ban dang yeu o prerequisite A, nen quay lai hoc A truoc khi tiep tuc B.
```

## 10. Graph Quality Tools

Lay cam hung tu Neo4j repo:

- duplicate node detector,
- merge duplicate nodes,
- orphan node detector,
- schema validator,
- reprocess document,
- retry from failed chunk,
- graph quality score.

## 11. Multi-Document Knowledge Base

Tuong lai nen ho tro:

- upload nhieu tai lieu cung subject,
- merge graph giua cac tai lieu,
- phat hien node trung,
- so sanh cach cac tai lieu giai thich cung concept,
- tao "personal textbook".

## 12. Teacher Mode

Cho giao vien:

- upload slide/giao trinh,
- tao module,
- tao quiz,
- sua graph,
- export lesson plan,
- theo doi lop hoc.
