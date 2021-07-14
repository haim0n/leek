import React, {useMemo} from "react";
import {Card, Input, Row, Select, Button, Form, InputNumber} from "antd";

import {useApplication} from "../../context/ApplicationProvider";
import {TaskStateClosable} from "../tags/TaskState";
import {badgedOption} from "../tags/BadgedOption";

const {Option} = Select;
const FormItem = Form.Item;

interface TasksFilterContextData {
    onFilter(value: {});
}

const TaskAttributesFilter: React.FC<TasksFilterContextData> = (props: TasksFilterContextData) => {
    const {seenTasks, seenWorkers, seenTaskStates, seenRoutingKeys, seenQueues} = useApplication();
    const [form] = Form.useForm();

    // UI Callbacks
    function handleReset() {
        form.resetFields();
        form.submit()
    }

    function onSubmit(filters) {
        props.onFilter(filters)
    }

    const memoizedTaskNameOptions = useMemo(() => {
        // memoize this because it's common to have many different task names, which causes the dropdown to be very laggy.
        // This is a known problem in Ant Design
        return seenTasks.map((task, key) => badgedOption(task))
    }, [seenTasks]) 

    return (
        <Card title={
            <Button size="small" type="primary" onClick={form.submit}>
                Filter
            </Button>
        } size={"small"}
              extra={<Button onClick={handleReset} size="small">Reset</Button>}
              style={{width: "100%"}}
        >
            <Form style={{width: "100%"}} form={form} onFinish={onSubmit}
                  initialValues={{runtime_op: "gte", retries_op: "gte"}}>
                <Row>
                    <FormItem name="uuid" style={{width: "100%"}}>
                        <Input placeholder="uuid" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="name" style={{width: "100%"}}>
                        <Select placeholder="Name"
                                mode="multiple"
                                style={{width: "100%"}}
                                allowClear
                                showSearch
                                dropdownMatchSelectWidth={false}>
                            {memoizedTaskNameOptions}
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="state" style={{width: "100%"}}>
                        <Select placeholder="State"
                                mode="multiple"
                                tagRender={TaskStateClosable}
                                style={{width: "100%"}}
                                allowClear>
                            {
                                seenTaskStates.map((state, key) => badgedOption(state))
                            }
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="routing_key" style={{width: "100%"}}>
                        <Select placeholder="Routing key"
                                mode="multiple"
                                style={{width: "100%"}}
                                allowClear>
                            {
                                seenRoutingKeys.map((rq, key) => badgedOption(rq))
                            }
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="queue" style={{width: "100%"}}>
                        <Select placeholder="Queue"
                                mode="multiple"
                                style={{width: "100%"}}
                                allowClear>
                            {
                                seenQueues.map((queue, key) => badgedOption(queue))
                            }
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="worker" style={{width: "100%"}}>
                        <Select placeholder="Worker"
                                mode="multiple"
                                style={{width: "100%"}}
                                allowClear>
                            {
                                seenWorkers.map((worker, key) => badgedOption(worker))
                            }
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <Input.Group compact>
                        <FormItem name="runtime_op" style={{width: "30%"}}>
                            <Select style={{width: '100%'}}>
                                <Option value="gte">{"gte"}</Option>
                                <Option value="lte">{"lte"}</Option>
                            </Select>
                        </FormItem>
                        <FormItem name="runtime" style={{width: "70%"}}>
                            <InputNumber style={{width: '100%'}}
                                         min={0} max={10000} step={0.0001}
                                         placeholder="Runtime"
                            />
                        </FormItem>

                    </Input.Group>
                </Row>
                <Row>
                    <Input.Group compact>
                        <FormItem name="retries_op" style={{width: "30%"}}>
                            <Select style={{width: '100%'}}>
                                <Option value="gte">{"gte"}</Option>
                                <Option value="lte">{"lte"}</Option>
                            </Select>
                        </FormItem>
                        <FormItem name="retries" style={{width: "70%"}}>
                            <InputNumber style={{width: '100%'}}
                                         min={0} max={10000} step={1}
                                         placeholder="Retries"
                            />
                        </FormItem>
                    </Input.Group>
                </Row>
                <Row>
                    <FormItem name="exception" style={{width: "100%"}}>
                        <Input placeholder="Exception" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="traceback" style={{width: "100%"}}>
                        <Input placeholder="Traceback" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="args" style={{width: "100%"}}>
                        <Input placeholder="args" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="kwargs" style={{width: "100%"}}>
                        <Input placeholder="kwargs" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="result" style={{width: "100%"}}>
                        <Input placeholder="Result" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="revocation_reason" style={{width: "100%"}}>
                        <Select placeholder="Revocation reason" allowClear>
                            <Option value="expired">{"Expired"}</Option>
                            <Option value="terminated">{"Terminated"}</Option>
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="rejection_outcome" style={{width: "100%"}}>
                        <Select placeholder="Rejection outcome" allowClear>
                            <Option value="requeued">{"Requeued"}</Option>
                            <Option value="ignored">{"Ignored"}</Option>
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="root_id" style={{width: "100%"}}>
                        <Input placeholder="Root id" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="parent_id" style={{width: "100%"}}>
                        <Input placeholder="Parent id" allowClear/>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="root_name" style={{width: "100%"}}>
                        <Select placeholder="Root name (soon)" disabled={true}>
                        </Select>
                    </FormItem>
                </Row>
                <Row>
                    <FormItem name="parent_name" style={{width: "100%"}}>
                        <Select placeholder="Parent name (soon)" disabled={true}>
                        </Select>
                    </FormItem>
                </Row>
            </Form>
        </Card>
    );
};

export default TaskAttributesFilter
